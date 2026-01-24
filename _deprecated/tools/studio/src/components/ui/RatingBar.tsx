import { clsx } from 'clsx';

export const RatingBar = ({
    value,
    max = 5,
    onChange,
    activeColor = "bg-accent",
    passiveColor = "bg-white/10",
    hoverColor = "hover:bg-white/20",
    mini = false
}: {
    value: number,
    max?: number,
    onChange?: (val: number) => void,
    activeColor?: string,
    passiveColor?: string,
    hoverColor?: string,
    mini?: boolean
}) => {
    return (
        <div className={clsx("flex gap-0.5", mini ? "h-1.5 w-max" : "h-3 mt-1", onChange && "cursor-pointer group/rating select-none")}>
            {Array.from({ length: max }, (_, i) => i + 1).map(v => (
                <div
                    key={v}
                    onClick={(e) => {
                        if (onChange) {
                            e.stopPropagation();
                            onChange(v);
                        }
                    }}
                    className={clsx(
                        "rounded-[1px] transition-all duration-200 border border-transparent",
                        mini ? "w-2" : "flex-1",
                        onChange && "hover:border-white/50 hover:scale-110",
                        value >= v ? activeColor : passiveColor,
                        value >= v && !mini && "shadow-[0_0_8px_rgba(0,0,0,0.5)]",
                        onChange && value < v && hoverColor
                    )}
                />
            ))}
        </div>
    );
};
