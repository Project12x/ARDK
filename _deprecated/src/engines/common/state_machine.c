/**
 * =============================================================================
 * ARDK State Machine
 * =============================================================================
 * Simple state machine for game flow control.
 * Supports enter/update/exit callbacks per state.
 * =============================================================================
 */

#include "common.h"

void state_machine_init(state_machine_t* sm)
{
    u8 i;

    sm->current = STATE_BOOT;
    sm->next = STATE_BOOT;
    sm->transition_pending = 0;

    /* Clear all handlers */
    for (i = 0; i < STATE_COUNT; i++) {
        sm->handlers[i].enter = NULL;
        sm->handlers[i].update = NULL;
        sm->handlers[i].exit = NULL;
    }
}

void state_machine_register(state_machine_t* sm, game_state_t state,
                           state_enter_fn enter, state_update_fn update,
                           state_exit_fn exit)
{
    if (state >= STATE_COUNT) return;

    sm->handlers[state].enter = enter;
    sm->handlers[state].update = update;
    sm->handlers[state].exit = exit;
}

void state_machine_change(state_machine_t* sm, game_state_t new_state)
{
    if (new_state >= STATE_COUNT) return;

    sm->next = new_state;
    sm->transition_pending = 1;
}

void state_machine_update(state_machine_t* sm)
{
    /* Handle pending transition */
    if (sm->transition_pending) {
        sm->transition_pending = 0;

        /* Exit current state */
        if (sm->handlers[sm->current].exit != NULL) {
            sm->handlers[sm->current].exit();
        }

        /* Enter new state */
        sm->current = sm->next;
        if (sm->handlers[sm->current].enter != NULL) {
            sm->handlers[sm->current].enter();
        }
    }

    /* Update current state */
    if (sm->handlers[sm->current].update != NULL) {
        sm->handlers[sm->current].update();
    }
}
