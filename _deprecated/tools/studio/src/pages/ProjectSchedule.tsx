import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { enUS } from 'date-fns/locale';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../lib/db';
import { useNavigate } from 'react-router-dom';
import { useState, useMemo, useEffect } from 'react';
import { Calendar as CalendarIcon } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useDroppable, useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';

// Droppable Cell Wrapper
const DroppableDateCell = ({ value, children }: any) => {
    const { isOver, setNodeRef } = useDroppable({
        id: `calendar-cell-${format(value, 'yyyy-MM-dd')}`,
    });

    return (
        <div ref={setNodeRef} className={clsx("h-full relative", isOver && "bg-green-500/20 box-shadow-inner transition-colors")}>
            {isOver && <div className="absolute inset-0 border-2 border-green-500 rounded pointer-events-none" />}
            {children}
        </div>
    );
};

// Draggable Event Wrapper
const DraggableEvent = ({ event, title, isAllDay, localizer, continuesPrior, continuesAfter, ...props }: any) => {
    // Only make tasks and projects draggable
    const isDraggable = event.type === 'task' || event.type === 'project';

    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `calendar-${event.type}-${event.id}`,
        data: {
            type: `${event.type}-item`, // task-item or project-item
            item: event.resource,
            from: 'calendar'
        },
        disabled: !isDraggable
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 9999,
        opacity: 0.8,
        position: 'relative' as const
    } : undefined;

    return (
        <div
            ref={isDraggable ? setNodeRef : null}
            style={style}
            {...(isDraggable ? listeners : {})}
            {...(isDraggable ? attributes : {})}
            className={clsx(isDragging && "opacity-50")}
            title={title}
        >
            {title}
        </div>
    );
};

const locales = {
    'en-US': enUS,
};

const localizer = dateFnsLocalizer({
    format,
    parse,
    startOfWeek,
    getDay,
    locales,
});

// Weather Code Map (Simplified)
function getWeatherIcon(code: number) {
    if (code === 0) return '☀️';
    if (code <= 3) return '⛅';
    if (code <= 48) return '🌫️'; // Fog
    if (code <= 67) return '🌧️'; // Rain
    if (code <= 77) return '❄️'; // Snow
    if (code <= 82) return '🌧️'; // Showers
    return '⛈️';
}

export function ProjectSchedule() {
    const navigate = useNavigate();
    const projects = useLiveQuery(() => db.projects.toArray()) || [];
    // Fetch scheduled tasks
    const tasks = useLiveQuery(() => db.project_tasks.filter(t => !!t.scheduled_date).toArray()) || [];
    const [view, setView] = useState<'month' | 'week' | 'day'>('month');
    const [weatherEvents, setWeatherEvents] = useState<any[]>([]);

    // Fetch Weather Forecast
    useEffect(() => {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(async (position) => {
                const { latitude, longitude } = position.coords;
                try {
                    const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max&temperature_unit=fahrenheit&timezone=auto`);
                    const data = await res.json();

                    if (data.daily) {
                        const newEvents = data.daily.time.map((time: string, i: number) => {
                            const maxTemp = Math.round(data.daily.temperature_2m_max[i]);
                            const precipProb = data.daily.precipitation_probability_max?.[i] || 0;
                            const code = data.daily.weathercode[i];
                            const icon = getWeatherIcon(code);

                            // Create a date object in local time
                            const dateParts = time.split('-');
                            const date = new Date(Number(dateParts[0]), Number(dateParts[1]) - 1, Number(dateParts[2]));

                            // Title Format: "☀️ 75°F 💧30%"
                            let title = `${icon} ${maxTemp}°F`;
                            if (precipProb > 20) {
                                title += ` 💧${precipProb}%`;
                            }

                            return {
                                id: `weather-${time}`,
                                title,
                                start: date,
                                end: date,
                                allDay: true,
                                type: 'weather',
                                status: 'weather'
                            };
                        });
                        setWeatherEvents(newEvents);
                    }
                } catch (e) {
                    console.error("Weather fetch failed", e);
                }
            });
        }
    }, []);

    // Transform Projects to Events
    const projectEvents = useMemo(() => {
        return projects
            .filter(p => !!p.target_completion_date) // ONLY show projects with manually entered target dates.
            .map(p => {
                const endDate = new Date(p.target_completion_date!);
                return {
                    id: p.id,
                    title: p.title,
                    start: endDate,
                    end: endDate,
                    resource: p,
                    status: p.status,
                    allDay: true,
                    type: 'project'
                };
            });
    }, [projects]);

    // Transform Tasks to Events
    const taskEvents = useMemo(() => {
        return tasks.map(t => {
            const date = new Date(t.scheduled_date!);
            if (t.scheduled_time) {
                const [h, m] = t.scheduled_time.split(':');
                date.setHours(Number(h), Number(m));
            }
            return {
                id: `task-${t.id}`,
                title: t.title,
                start: date,
                end: date,
                status: t.status,
                allDay: !t.scheduled_time,
                type: 'task',
                resource: t
            };
        });
    }, [tasks]);

    const events = [...projectEvents, ...taskEvents, ...weatherEvents];

    // Custom Event Styling
    const eventPropGetter = (event: any) => {
        let backgroundColor = '#333';
        let color = 'white';
        let border = '0px';

        if (event.type === 'weather') {
            backgroundColor = 'rgba(255,255,255,0.05)';
            color = '#fbbf24'; // Amber
            border = '1px dashed rgba(255,255,255,0.1)';
        } else if (event.type === 'task') {
            backgroundColor = '#2563eb'; // Blue for tasks
            if (event.status === 'completed') backgroundColor = '#059669'; // Green if done
        } else {
            switch (event.status) {
                case 'completed': backgroundColor = '#10b981'; break; // Green
                case 'active': backgroundColor = '#3b82f6'; break; // Blue
                case 'planning': backgroundColor = '#a855f7'; break; // Purple
                case 'paused': backgroundColor = '#f59e0b'; break; // Orange
            }
        }

        return {
            style: {
                backgroundColor,
                borderRadius: '4px',
                opacity: 0.9,
                color,
                border,
                display: 'block',
                fontSize: event.type === 'weather' ? '0.75rem' : '0.8rem',
                fontWeight: event.type === 'weather' ? 'normal' : 'bold'
            }
        };
    };

    const components = useMemo(() => ({
        dateCellWrapper: DroppableDateCell,
        event: DraggableEvent
    }), []);

    return (
        <div className="h-full flex flex-col space-y-4">
            <div className="flex justify-between items-center bg-black/40 p-4 border-b border-white/10">
                <div className="flex items-center gap-3">
                    <CalendarIcon className="text-accent" size={24} />
                    <h1 className="text-2xl font-bold tracking-tight text-white">Master Schedule</h1>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setView('month')} className={view === 'month' ? 'bg-accent text-black' : ''}>Month</Button>
                    <Button variant="outline" size="sm" onClick={() => setView('week')} className={view === 'week' ? 'bg-accent text-black' : ''}>Week</Button>
                    <Button variant="outline" size="sm" onClick={() => setView('day')} className={view === 'day' ? 'bg-accent text-black' : ''}>Day</Button>
                </div>
            </div>

            <div className="flex-1 bg-neutral-900/50 border border-white/10 rounded-xl p-4 shadow-inner overflow-hidden relative">
                <style>{`
                    .rbc-calendar { color: #aaa; font-family: 'Inter', monospace; }
                    .rbc-toolbar button { color: #fff; border: 1px solid #333; }
                    .rbc-toolbar button:hover { bg-color: #333; }
                    .rbc-toolbar button.rbc-active { background-color: #3b82f6; color: white; border-color: #3b82f6; }
                    .rbc-off-range-bg { background: #111; }
                    .rbc-month-view, .rbc-time-view, .rbc-agenda-view { border: 1px solid #333; }
                    .rbc-header { border-bottom: 1px solid #333; padding: 10px; font-weight: 700; color: #fff; }
                    .rbc-day-bg + .rbc-day-bg { border-left: 1px solid #333; }
                    .rbc-month-row + .rbc-month-row { border-top: 1px solid #333; }
                    .rbc-date-cell { padding: 4px; font-size: 0.8rem; }
                    .rbc-today { background-color: rgba(59, 130, 246, 0.1); }
                    .rbc-event { background-color: transparent; padding: 0; } 
                `}</style>
                <Calendar
                    localizer={localizer}
                    events={events}
                    startAccessor="start"
                    endAccessor="end"
                    style={{ height: '100%' }}
                    view={view}
                    onView={(v) => setView(v as any)}
                    onSelectEvent={(event) => {
                        if (event.type === 'project') navigate(`/projects/${event.resource.id}`);
                        // TODO: Maybe open task modal on click?
                    }}
                    eventPropGetter={eventPropGetter}
                    components={components}
                    popup
                />
            </div>
        </div>
    );
}
