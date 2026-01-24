"""
Animation Finite State Machine Generator for SGDK.

This module generates C code for animation state machines that can be
directly compiled into Genesis/Mega Drive games using SGDK. It bridges
the gap between artist-created animations and game code.

Key Features:
    - Define animation states (idle, walk, attack, etc.)
    - Specify transitions with conditions (input, timer, event)
    - Generate SGDK-compatible C header and source files
    - Import/export FSM definitions as JSON for tooling
    - Validate state machine completeness and reachability

Why Use Animation FSMs:
    - Decouple animation logic from game logic
    - Artists can define animation flows without coding
    - Automatic transition handling (no manual SPR_setAnim calls)
    - Built-in support for one-shot animations with callbacks
    - Consistent animation behavior across entities

Usage:
    >>> from pipeline.animation_fsm import AnimationFSM, AnimationState, Transition
    >>>
    >>> # Define states
    >>> idle = AnimationState("idle", anim_index=0, loop=True)
    >>> walk = AnimationState("walk", anim_index=1, loop=True)
    >>> attack = AnimationState("attack", anim_index=2, loop=False)
    >>>
    >>> # Define transitions
    >>> idle.add_transition(Transition("walk", condition="input_move"))
    >>> idle.add_transition(Transition("attack", condition="input_attack"))
    >>> walk.add_transition(Transition("idle", condition="!input_move"))
    >>> attack.add_transition(Transition("idle", condition="anim_complete"))
    >>>
    >>> # Create FSM
    >>> fsm = AnimationFSM("player", initial_state="idle")
    >>> fsm.add_state(idle)
    >>> fsm.add_state(walk)
    >>> fsm.add_state(attack)
    >>>
    >>> # Generate C code
    >>> fsm.export_sgdk_header("player_anim.h")
    >>> fsm.export_sgdk_source("player_anim.c")

Generated Code Example:
    ```c
    // player_anim.h
    typedef enum {
        PLAYER_ANIM_IDLE = 0,
        PLAYER_ANIM_WALK = 1,
        PLAYER_ANIM_ATTACK = 2,
        PLAYER_ANIM_COUNT
    } PlayerAnimState;

    void Player_AnimFSM_init(Sprite* sprite);
    void Player_AnimFSM_update(Sprite* sprite, u16 input);
    PlayerAnimState Player_AnimFSM_getState(void);
    ```

Integration with SGDK:
    The generated code uses SGDK's SPR_setAnim() for animation changes
    and provides callbacks for animation completion events.

Phase Implementation:
    - Phase 2.2.2: Animation FSM code generation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from enum import Enum
import json
import re


class ConditionType(Enum):
    """Types of conditions that can trigger transitions.

    Attributes:
        INPUT: Triggered by controller input (e.g., "input_move", "input_attack").
        TIMER: Triggered after a duration (e.g., "timer_500ms").
        EVENT: Triggered by game events (e.g., "event_hit", "event_land").
        ANIM_COMPLETE: Triggered when current animation finishes.
        CUSTOM: Custom condition evaluated by user code.
    """
    INPUT = "input"
    TIMER = "timer"
    EVENT = "event"
    ANIM_COMPLETE = "anim_complete"
    CUSTOM = "custom"


@dataclass
class Transition:
    """A transition between animation states.

    Defines when and how to move from one animation state to another.
    Conditions can be simple (single check) or compound (AND/OR).

    Attributes:
        target_state: Name of the state to transition to.
        condition: Condition string (e.g., "input_move", "anim_complete").
        priority: Higher priority transitions are checked first (default 0).
        callback: Optional C function to call on transition.

    Condition Syntax:
        - "input_X": Check if input flag X is set
        - "!input_X": Check if input flag X is NOT set
        - "timer_Nms": Trigger after N milliseconds in state
        - "anim_complete": Trigger when animation finishes (loop=False)
        - "event_X": Trigger on game event X
        - Custom conditions are passed to user-defined check function

    Example:
        >>> # Transition to walk when move input is pressed
        >>> t1 = Transition("walk", condition="input_move")
        >>>
        >>> # Return to idle when attack animation finishes
        >>> t2 = Transition("idle", condition="anim_complete")
        >>>
        >>> # High-priority interrupt for damage
        >>> t3 = Transition("hurt", condition="event_damage", priority=10)
    """
    target_state: str
    condition: str = "true"
    priority: int = 0
    callback: Optional[str] = None

    def parse_condition(self) -> tuple:
        """Parse condition string into type and parameters.

        Returns:
            Tuple of (ConditionType, negated: bool, param: str)
        """
        cond = self.condition.strip()
        negated = cond.startswith("!")
        if negated:
            cond = cond[1:]

        if cond == "anim_complete":
            return (ConditionType.ANIM_COMPLETE, negated, None)
        elif cond.startswith("input_"):
            return (ConditionType.INPUT, negated, cond[6:])
        elif cond.startswith("timer_"):
            return (ConditionType.TIMER, negated, cond[6:])
        elif cond.startswith("event_"):
            return (ConditionType.EVENT, negated, cond[6:])
        elif cond == "true":
            return (ConditionType.CUSTOM, False, "TRUE")
        else:
            return (ConditionType.CUSTOM, negated, cond)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "target": self.target_state,
            "condition": self.condition,
            "priority": self.priority,
            "callback": self.callback,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transition':
        """Create from dictionary (JSON deserialization)."""
        return cls(
            target_state=data.get("target", ""),
            condition=data.get("condition", "true"),
            priority=data.get("priority", 0),
            callback=data.get("callback"),
        )


@dataclass
class AnimationState:
    """A single state in the animation state machine.

    Represents one animation (e.g., "idle", "walk", "attack") with
    its properties and outgoing transitions.

    Attributes:
        name: Unique state identifier (used in C enum).
        anim_index: SGDK animation index (SPR_setAnim parameter).
        loop: Whether the animation loops (True) or plays once (False).
        transitions: List of possible transitions from this state.
        on_enter: Optional C callback when entering this state.
        on_exit: Optional C callback when leaving this state.
        on_frame: Optional C callback on each animation frame.
        metadata: Additional data for tooling (not exported to C).

    Example:
        >>> # Looping idle animation
        >>> idle = AnimationState("idle", anim_index=0, loop=True)
        >>>
        >>> # One-shot attack with callback
        >>> attack = AnimationState(
        ...     "attack",
        ...     anim_index=2,
        ...     loop=False,
        ...     on_enter="Attack_onStart",
        ...     on_exit="Attack_onEnd"
        ... )
    """
    name: str
    anim_index: int = 0
    loop: bool = True
    transitions: List[Transition] = field(default_factory=list)
    on_enter: Optional[str] = None
    on_exit: Optional[str] = None
    on_frame: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_transition(self, transition: Transition) -> None:
        """Add a transition from this state."""
        self.transitions.append(transition)
        # Keep sorted by priority (highest first)
        self.transitions.sort(key=lambda t: -t.priority)

    def get_transition_targets(self) -> Set[str]:
        """Get all states this state can transition to."""
        return {t.target_state for t in self.transitions}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "anim_index": self.anim_index,
            "loop": self.loop,
            "transitions": [t.to_dict() for t in self.transitions],
            "on_enter": self.on_enter,
            "on_exit": self.on_exit,
            "on_frame": self.on_frame,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimationState':
        """Create from dictionary (JSON deserialization)."""
        state = cls(
            name=data.get("name", "unknown"),
            anim_index=data.get("anim_index", 0),
            loop=data.get("loop", True),
            on_enter=data.get("on_enter"),
            on_exit=data.get("on_exit"),
            on_frame=data.get("on_frame"),
            metadata=data.get("metadata", {}),
        )
        for t_data in data.get("transitions", []):
            state.add_transition(Transition.from_dict(t_data))
        return state


@dataclass
class FSMValidationResult:
    """Result of FSM validation.

    Attributes:
        valid: True if FSM passed all checks.
        errors: List of critical errors (FSM won't work).
        warnings: List of potential issues (FSM may work incorrectly).
    """
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = []
        if self.valid:
            lines.append("[OK] FSM validation PASSED")
        else:
            lines.append("[FAIL] FSM validation FAILED")

        if self.errors:
            lines.append("\nErrors:")
            for e in self.errors:
                lines.append(f"  [X] {e}")

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  [!] {w}")

        return "\n".join(lines)


class AnimationFSM:
    """Animation Finite State Machine for SGDK code generation.

    Manages a complete animation state machine with states, transitions,
    and code generation capabilities.

    Example:
        >>> fsm = AnimationFSM("player", initial_state="idle")
        >>> fsm.add_state(AnimationState("idle", 0, loop=True))
        >>> fsm.add_state(AnimationState("walk", 1, loop=True))
        >>>
        >>> # Validate before export
        >>> result = fsm.validate()
        >>> if result.valid:
        ...     fsm.export_sgdk("src/player_anim")
    """

    def __init__(self, name: str, initial_state: str = None):
        """Initialize the FSM.

        Args:
            name: FSM name (used for C identifiers, e.g., "player" → Player_AnimFSM).
            initial_state: Name of the starting state.
        """
        self.name = name
        self.initial_state = initial_state
        self.states: Dict[str, AnimationState] = {}
        self.metadata: Dict[str, Any] = {}

        # C code generation options
        self.prefix = self._to_pascal_case(name)
        self.include_guards = True
        self.generate_debug = False

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase for C identifiers."""
        # Handle snake_case
        parts = name.replace("-", "_").split("_")
        return "".join(p.capitalize() for p in parts)

    def _to_upper_snake(self, name: str) -> str:
        """Convert name to UPPER_SNAKE_CASE for C constants."""
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()

    def add_state(self, state: AnimationState) -> None:
        """Add a state to the FSM.

        Args:
            state: AnimationState to add.

        Raises:
            ValueError: If state with same name already exists.
        """
        if state.name in self.states:
            raise ValueError(f"State '{state.name}' already exists in FSM")
        self.states[state.name] = state

        # Auto-set initial state if not set
        if self.initial_state is None:
            self.initial_state = state.name

    def get_state(self, name: str) -> Optional[AnimationState]:
        """Get a state by name."""
        return self.states.get(name)

    def validate(self) -> FSMValidationResult:
        """Validate the FSM for completeness and correctness.

        Checks:
            - Initial state exists
            - All transition targets exist
            - No orphan states (unreachable from initial)
            - One-shot animations have exit transitions

        Returns:
            FSMValidationResult with errors and warnings.
        """
        errors = []
        warnings = []

        # Check initial state
        if not self.initial_state:
            errors.append("No initial state defined")
        elif self.initial_state not in self.states:
            errors.append(f"Initial state '{self.initial_state}' does not exist")

        # Check transition targets
        for state_name, state in self.states.items():
            for trans in state.transitions:
                if trans.target_state not in self.states:
                    errors.append(
                        f"State '{state_name}' has transition to "
                        f"non-existent state '{trans.target_state}'"
                    )

        # Check reachability (find orphan states)
        if self.initial_state and self.initial_state in self.states:
            reachable = self._find_reachable_states()
            for state_name in self.states:
                if state_name not in reachable:
                    warnings.append(f"State '{state_name}' is unreachable from initial state")

        # Check one-shot animations have exit conditions
        for state_name, state in self.states.items():
            if not state.loop:
                has_anim_complete = any(
                    t.condition == "anim_complete" for t in state.transitions
                )
                if not has_anim_complete:
                    warnings.append(
                        f"One-shot state '{state_name}' has no 'anim_complete' transition"
                    )

        # Check for duplicate anim_index
        indices = {}
        for state_name, state in self.states.items():
            if state.anim_index in indices:
                warnings.append(
                    f"States '{indices[state.anim_index]}' and '{state_name}' "
                    f"share anim_index {state.anim_index}"
                )
            indices[state.anim_index] = state_name

        valid = len(errors) == 0
        return FSMValidationResult(valid=valid, errors=errors, warnings=warnings)

    def _find_reachable_states(self) -> Set[str]:
        """Find all states reachable from initial state (BFS)."""
        if not self.initial_state:
            return set()

        visited = set()
        queue = [self.initial_state]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            state = self.states.get(current)
            if state:
                for trans in state.transitions:
                    if trans.target_state not in visited:
                        queue.append(trans.target_state)

        return visited

    def export_sgdk_header(self, output_path: str) -> str:
        """Generate SGDK-compatible C header file.

        Args:
            output_path: Path to write the .h file.

        Returns:
            Generated header content.
        """
        lines = []
        guard = f"{self._to_upper_snake(self.name)}_ANIM_H"

        # Standard C header guard to prevent multiple inclusion
        if self.include_guards:
            lines.append(f"#ifndef {guard}")
            lines.append(f"#define {guard}")
            lines.append("")

        # Includes
        lines.append("#include <genesis.h>")
        lines.append("")

        # State enum
        lines.append(f"// Animation states for {self.name}")
        lines.append("typedef enum {")
        for i, state_name in enumerate(self.states.keys()):
            enum_name = f"{self._to_upper_snake(self.name)}_ANIM_{self._to_upper_snake(state_name)}"
            lines.append(f"    {enum_name} = {i},")
        lines.append(f"    {self._to_upper_snake(self.name)}_ANIM_COUNT")
        lines.append(f"}} {self.prefix}AnimState;")
        lines.append("")

        # Input flags - bitmask constants for controller/game input
        # Automatically collected from "input_X" conditions in transitions
        input_flags = self._collect_input_flags()
        if input_flags:
            lines.append("// Input flags for FSM transitions")
            for i, flag in enumerate(sorted(input_flags)):
                flag_name = f"{self._to_upper_snake(self.name)}_INPUT_{self._to_upper_snake(flag)}"
                lines.append(f"#define {flag_name} (1 << {i})")
            lines.append("")

        # Function declarations
        lines.append("// FSM lifecycle functions")
        lines.append(f"void {self.prefix}_AnimFSM_init(Sprite* sprite);")
        lines.append(f"void {self.prefix}_AnimFSM_update(Sprite* sprite, u16 input);")
        lines.append(f"{self.prefix}AnimState {self.prefix}_AnimFSM_getState(void);")
        lines.append(f"void {self.prefix}_AnimFSM_setState(Sprite* sprite, {self.prefix}AnimState state);")
        lines.append(f"bool {self.prefix}_AnimFSM_isAnimComplete(void);")
        lines.append("")

        # Event trigger function
        event_flags = self._collect_event_flags()
        if event_flags:
            lines.append("// Event triggers")
            lines.append(f"void {self.prefix}_AnimFSM_triggerEvent(Sprite* sprite, u16 event);")
            lines.append("")
            for i, flag in enumerate(sorted(event_flags)):
                flag_name = f"{self._to_upper_snake(self.name)}_EVENT_{self._to_upper_snake(flag)}"
                lines.append(f"#define {flag_name} (1 << {i})")
            lines.append("")

        # Close guard
        if self.include_guards:
            lines.append(f"#endif // {guard}")
            lines.append("")

        content = "\n".join(lines)

        # Write file
        with open(output_path, 'w') as f:
            f.write(content)

        print(f"[EXPORT] SGDK header: {output_path}")
        return content

    def export_sgdk_source(self, output_path: str, header_name: str = None) -> str:
        """Generate SGDK-compatible C source file.

        Args:
            output_path: Path to write the .c file.
            header_name: Name of header to include (default: derived from output_path).

        Returns:
            Generated source content.
        """
        if header_name is None:
            header_name = output_path.replace(".c", ".h").split("/")[-1].split("\\")[-1]

        lines = []

        # Includes
        lines.append(f'#include "{header_name}"')
        lines.append("")

        # Static state variables
        lines.append("// FSM state")
        lines.append(f"static {self.prefix}AnimState current_state = 0;")
        lines.append("static bool anim_complete = FALSE;")
        lines.append("static u16 state_timer = 0;")
        lines.append("static u16 pending_events = 0;")
        lines.append("")

        # Animation info table
        lines.append("// Animation configuration")
        lines.append("static const struct {")
        lines.append("    u8 anim_index;")
        lines.append("    bool loop;")
        lines.append(f"}} anim_config[{self._to_upper_snake(self.name)}_ANIM_COUNT] = {{")
        for state in self.states.values():
            loop_str = "TRUE" if state.loop else "FALSE"
            lines.append(f"    {{ {state.anim_index}, {loop_str} }},  // {state.name}")
        lines.append("};")
        lines.append("")

        # Animation complete callback
        lines.append("// Animation complete callback (set via SPR_setAnimationComplete)")
        lines.append(f"static void {self.prefix}_onAnimComplete(Sprite* sprite) {{")
        lines.append("    (void)sprite;  // Unused in base implementation")
        lines.append("    anim_complete = TRUE;")
        lines.append("}")
        lines.append("")

        # Init function
        lines.append(f"void {self.prefix}_AnimFSM_init(Sprite* sprite) {{")
        if self.initial_state:
            initial_enum = f"{self._to_upper_snake(self.name)}_ANIM_{self._to_upper_snake(self.initial_state)}"
            lines.append(f"    current_state = {initial_enum};")
        else:
            lines.append("    current_state = 0;")
        lines.append("    anim_complete = FALSE;")
        lines.append("    state_timer = 0;")
        lines.append("    pending_events = 0;")
        lines.append("")
        lines.append("    // Set initial animation")
        lines.append("    SPR_setAnim(sprite, anim_config[current_state].anim_index);")
        lines.append(f"    SPR_setAnimationComplete(sprite, {self.prefix}_onAnimComplete);")
        lines.append("}")
        lines.append("")

        # Get state function
        lines.append(f"{self.prefix}AnimState {self.prefix}_AnimFSM_getState(void) {{")
        lines.append("    return current_state;")
        lines.append("}")
        lines.append("")

        # Is anim complete function
        lines.append(f"bool {self.prefix}_AnimFSM_isAnimComplete(void) {{")
        lines.append("    return anim_complete;")
        lines.append("}")
        lines.append("")

        # Set state function
        lines.append(f"void {self.prefix}_AnimFSM_setState(Sprite* sprite, {self.prefix}AnimState state) {{")
        lines.append(f"    if (state >= {self._to_upper_snake(self.name)}_ANIM_COUNT) return;")
        lines.append("    if (state == current_state) return;")
        lines.append("")
        lines.append("    current_state = state;")
        lines.append("    anim_complete = FALSE;")
        lines.append("    state_timer = 0;")
        lines.append("    SPR_setAnim(sprite, anim_config[state].anim_index);")
        lines.append("}")
        lines.append("")

        # Event trigger function
        event_flags = self._collect_event_flags()
        if event_flags:
            lines.append(f"void {self.prefix}_AnimFSM_triggerEvent(Sprite* sprite, u16 event) {{")
            lines.append("    (void)sprite;  // May be used in custom handlers")
            lines.append("    pending_events |= event;")
            lines.append("}")
            lines.append("")

        # Update function with transition logic
        lines.append(f"void {self.prefix}_AnimFSM_update(Sprite* sprite, u16 input) {{")
        lines.append("    state_timer++;")
        lines.append("")
        lines.append("    switch (current_state) {")

        for state_name, state in self.states.items():
            state_enum = f"{self._to_upper_snake(self.name)}_ANIM_{self._to_upper_snake(state_name)}"
            lines.append(f"        case {state_enum}:")

            if state.transitions:
                for trans in state.transitions:
                    cond_code = self._generate_condition_code(trans)
                    target_enum = f"{self._to_upper_snake(self.name)}_ANIM_{self._to_upper_snake(trans.target_state)}"

                    lines.append(f"            if ({cond_code}) {{")
                    if trans.callback:
                        lines.append(f"                {trans.callback}();")
                    lines.append(f"                {self.prefix}_AnimFSM_setState(sprite, {target_enum});")

                    # Clear event if it was an event transition
                    cond_type, _, param = trans.parse_condition()
                    if cond_type == ConditionType.EVENT and param:
                        event_flag = f"{self._to_upper_snake(self.name)}_EVENT_{self._to_upper_snake(param)}"
                        lines.append(f"                pending_events &= ~{event_flag};")

                    lines.append("                break;")
                    lines.append("            }")

            lines.append("            break;")
            lines.append("")

        lines.append("        default:")
        lines.append("            break;")
        lines.append("    }")
        lines.append("}")
        lines.append("")

        content = "\n".join(lines)

        # Write file
        with open(output_path, 'w') as f:
            f.write(content)

        print(f"[EXPORT] SGDK source: {output_path}")
        return content

    def _generate_condition_code(self, trans: Transition) -> str:
        """Generate C condition code for a transition."""
        cond_type, negated, param = trans.parse_condition()
        prefix = "!" if negated else ""

        if cond_type == ConditionType.ANIM_COMPLETE:
            return f"{prefix}anim_complete"
        elif cond_type == ConditionType.INPUT:
            flag = f"{self._to_upper_snake(self.name)}_INPUT_{self._to_upper_snake(param)}"
            if negated:
                return f"!(input & {flag})"
            return f"(input & {flag})"
        elif cond_type == ConditionType.TIMER:
            # Parse timer value (e.g., "500ms" or "30" for frames)
            if param.endswith("ms"):
                # Convert ms to frames (assuming 60fps)
                ms = int(param[:-2])
                frames = (ms * 60) // 1000
            else:
                frames = int(param)
            return f"{prefix}(state_timer >= {frames})"
        elif cond_type == ConditionType.EVENT:
            flag = f"{self._to_upper_snake(self.name)}_EVENT_{self._to_upper_snake(param)}"
            if negated:
                return f"!(pending_events & {flag})"
            return f"(pending_events & {flag})"
        elif param == "TRUE":
            return "TRUE"
        else:
            # Custom condition - assume it's a function call
            return f"{prefix}{param}()"

    def _collect_input_flags(self) -> Set[str]:
        """Collect all input flags used in transitions."""
        flags = set()
        for state in self.states.values():
            for trans in state.transitions:
                cond_type, _, param = trans.parse_condition()
                if cond_type == ConditionType.INPUT and param:
                    flags.add(param)
        return flags

    def _collect_event_flags(self) -> Set[str]:
        """Collect all event flags used in transitions."""
        flags = set()
        for state in self.states.values():
            for trans in state.transitions:
                cond_type, _, param = trans.parse_condition()
                if cond_type == ConditionType.EVENT and param:
                    flags.add(param)
        return flags

    def export_sgdk(self, base_path: str) -> tuple:
        """Export both header and source files.

        Args:
            base_path: Base path without extension (e.g., "src/player_anim").

        Returns:
            Tuple of (header_content, source_content).
        """
        header_path = f"{base_path}.h"
        source_path = f"{base_path}.c"

        header = self.export_sgdk_header(header_path)
        source = self.export_sgdk_source(source_path)

        return (header, source)

    def to_dict(self) -> Dict[str, Any]:
        """Convert FSM to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "initial_state": self.initial_state,
            "states": [s.to_dict() for s in self.states.values()],
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert FSM to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def export_json(self, output_path: str) -> None:
        """Export FSM definition to JSON file."""
        with open(output_path, 'w') as f:
            f.write(self.to_json())
        print(f"[EXPORT] FSM JSON: {output_path}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnimationFSM':
        """Create FSM from dictionary (JSON deserialization)."""
        fsm = cls(
            name=data.get("name", "unnamed"),
            initial_state=data.get("initial_state"),
        )
        fsm.metadata = data.get("metadata", {})

        for state_data in data.get("states", []):
            fsm.add_state(AnimationState.from_dict(state_data))

        return fsm

    @classmethod
    def from_json(cls, json_str: str) -> 'AnimationFSM':
        """Create FSM from JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load_json(cls, input_path: str) -> 'AnimationFSM':
        """Load FSM definition from JSON file."""
        with open(input_path, 'r') as f:
            return cls.from_json(f.read())


def create_character_fsm(
    name: str,
    animations: List[str] = None,
    include_combat: bool = True,
) -> AnimationFSM:
    """Create a standard character animation FSM.

    Convenience function for creating typical game character FSMs with
    common states and transitions.

    Args:
        name: Character name (e.g., "player", "enemy").
        animations: List of animation names. Defaults to standard set.
        include_combat: Include attack/hurt/death states.

    Returns:
        Configured AnimationFSM.

    Example:
        >>> fsm = create_character_fsm("player")
        >>> fsm.export_sgdk("src/player_anim")
    """
    if animations is None:
        animations = ["idle", "walk"]
        if include_combat:
            animations.extend(["attack", "hurt", "death"])

    fsm = AnimationFSM(name, initial_state="idle")

    # Create states
    for i, anim_name in enumerate(animations):
        loop = anim_name in ("idle", "walk", "run")
        state = AnimationState(anim_name, anim_index=i, loop=loop)
        fsm.add_state(state)

    # Add standard transitions
    idle = fsm.get_state("idle")
    walk = fsm.get_state("walk")

    if idle and walk:
        idle.add_transition(Transition("walk", condition="input_move"))
        walk.add_transition(Transition("idle", condition="!input_move"))

    if include_combat:
        attack = fsm.get_state("attack")
        hurt = fsm.get_state("hurt")
        death = fsm.get_state("death")

        if idle and attack:
            idle.add_transition(Transition("attack", condition="input_attack"))
            attack.add_transition(Transition("idle", condition="anim_complete"))

        if hurt:
            # Hurt can interrupt most states
            for state in fsm.states.values():
                if state.name not in ("hurt", "death"):
                    state.add_transition(Transition("hurt", condition="event_damage", priority=5))
            hurt.add_transition(Transition("idle", condition="anim_complete"))

        if death:
            # Death from hurt
            if hurt:
                hurt.add_transition(Transition("death", condition="event_death", priority=10))
            # Death is final - no transitions out

    return fsm
