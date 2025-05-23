// Reusable popup module
export const PopupManager = {
    init() {
        if (!document.getElementById('notificationPopup')) {
            const popupHTML = `
                <div id="notificationPopup" class="popup-message">
                    <div id="popupTitle" class="popup-title"></div>
                    <div id="popupMessage" class="popup-content"></div>
                    <button class="close-button">&times;</button>
                </div>`;
            document.body.insertAdjacentHTML('beforeend', popupHTML);
        }
        
        // Add event listener for close button
        document.querySelector('#notificationPopup .close-button')?.addEventListener('click', () => {
            this.closePopup();
        });
    },

    showPopup(title, message, type = 'notice') {
        const popup = document.getElementById('notificationPopup');
        const titleElement = document.getElementById('popupTitle');
        const messageElement = document.getElementById('popupMessage');

        popup.className = 'popup-message';
        popup.classList.add(type);

        titleElement.textContent = title;
        messageElement.textContent = message;
        popup.classList.add('show');

        setTimeout(() => {
            this.closePopup();
        }, 4000);
    },

    closePopup() {
        const popup = document.getElementById('notificationPopup');
        popup.classList.add('hide');
        popup.addEventListener('animationend', () => {
            popup.classList.remove('show', 'hide');
        }, { once: true });
    }
};