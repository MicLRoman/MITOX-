// app.js

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();

    // --- Элементы DOM ---
    const appElement = document.getElementById('app');
    const complexesList = document.getElementById('complexes-list');
    const emptyListMessage = document.getElementById('empty-list-message');
    
    // Элементы модального окна
    const modal = document.getElementById('modal');
    const complexForm = document.getElementById('complex-form');
    const complexNameInput = document.getElementById('complex-name');
    const supplementsContainer = document.getElementById('supplements-container');

    // Кнопки
    const openModalBtn = document.getElementById('add-complex-btn');
    const addSupplementBtn = document.getElementById('add-supplement-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    
    // --- Функции ---

    // Функция для добавления нового поля "препарат + дозировка"
    const addSupplementField = () => {
        const supplementId = Date.now(); // Уникальный ID для элемента
        const newField = document.createElement('div');
        newField.classList.add('flex', 'items-center', 'space-x-2');
        newField.innerHTML = `
            <input type="text" name="supplement_name_${supplementId}" placeholder="Название препарата" class="w-2/3 px-3 py-2 border border-gray-300 rounded-md text-sm">
            <input type="text" name="supplement_dosage_${supplementId}" placeholder="Дозировка" class="w-1/3 px-3 py-2 border border-gray-300 rounded-md text-sm">
            <button type="button" class="remove-supplement-btn text-red-500 font-bold">X</button>
        `;
        supplementsContainer.appendChild(newField);

        // Добавляем обработчик для кнопки удаления
        newField.querySelector('.remove-supplement-btn').addEventListener('click', () => {
            newField.remove();
        });
    };

    // Функция для открытия модального окна
    const openModal = () => {
        // Сбрасываем форму перед открытием
        complexForm.reset();
        supplementsContainer.innerHTML = '';
        addSupplementField(); // Добавляем одно поле по умолчанию
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        appElement.style.filter = 'blur(5px)'; // Размываем фон
    };

    // Функция для закрытия модального окна
    const closeModal = () => {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        appElement.style.filter = 'none';
    };

    // Функция для отрисовки карточки комплекса на главном экране
    const renderComplexCard = (complex) => {
        // Убираем сообщение "у вас нет комплексов"
        if (emptyListMessage) {
            emptyListMessage.style.display = 'none';
        }

        const card = document.createElement('div');
        card.classList.add('bg-white', 'p-4', 'rounded-xl', 'shadow-md');
        
        let supplementsHtml = complex.supplements.map(sup => 
            `<li class="text-gray-600">${sup.name} - ${sup.dosage}</li>`
        ).join('');

        card.innerHTML = `
            <h2 class="font-bold text-lg">${complex.name}</h2>
            <ul class="list-disc list-inside mt-2">
                ${supplementsHtml}
            </ul>
        `;
        complexesList.appendChild(card);
    };

    // --- Обработчики событий ---

    openModalBtn.addEventListener('click', openModal);
    cancelBtn.addEventListener('click', closeModal);
    addSupplementBtn.addEventListener('click', addSupplementField);

    // Обработка отправки формы
    complexForm.addEventListener('submit', (event) => {
        event.preventDefault(); // Предотвращаем стандартную отправку формы

        const complexData = {
            name: complexNameInput.value,
            supplements: []
        };

        const supplementFields = supplementsContainer.querySelectorAll('div');
        supplementFields.forEach(field => {
            const nameInput = field.querySelector('input[placeholder="Название препарата"]');
            const dosageInput = field.querySelector('input[placeholder="Дозировка"]');
            
            if (nameInput.value && dosageInput.value) {
                complexData.supplements.push({
                    name: nameInput.value,
                    dosage: dosageInput.value
                });
            }
        });

        console.log('Собранные данные:', complexData); // Для отладки в консоли браузера
        
        // ВАЖНО: Здесь мы будем отправлять данные боту
        // tg.sendData(JSON.stringify(complexData));

        // Пока просто отрисуем карточку на экране и закроем окно
        renderComplexCard(complexData);
        closeModal();
        
        // Показываем уведомление об успехе
        tg.showAlert('Комплекс успешно сохранен!');
    });
});
