export const NotificationService = {
    async requestPermission() {
        if (!('Notification' in window)) {
            console.warn("Notifications not supported");
            return false;
        }
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    },

    send(title: string, options?: NotificationOptions) {
        if (!('Notification' in window)) return;

        if (Notification.permission === 'granted') {
            new Notification(title, {
                icon: '/pwa-192x192.png', // Assuming PWA icon exists or default
                badge: '/pwa-192x192.png',
                ...options
            });
        }
    }
};
