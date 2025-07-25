// js/app.js

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;

    // --- DOM Elements ---
    const appElement = document.getElementById('app');
    const complexesList = document.getElementById('complexes-list');
    const loadingMessage = document.getElementById('loading-message');
    const openModalBtn = document.getElementById('add-complex-btn');
    
    // Modal Elements
    const modal = document.getElementById('modal');
    const complexForm = document.getElementById('complex-form');
    const complexNameInput = document.getElementById('complex-name');
    const supplementsContainer = document.getElementById('supplements-container');
    const addSupplementBtn = document.getElementById('add-supplement-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const saveBtn = document.getElementById('save-btn'); // Получаем кнопку сохранения

    // --- Functions ---
    const renderComplexes = (complexes) => {
        complexesList.innerHTML = ''; 
        if (!complexes || complexes.length === 0) {
            complexesList.innerHTML = `<p class="text-center text-gray-500">У вас пока нет ни одного комплекса.</p>`;
        } else {
            complexes.forEach(complex => {
                const card = document.createElement('div');
                card.classList.add('bg-white', 'p-4', 'rounded-xl', 'shadow-md');
                
                let supplementsHtml = complex.supplements.map(sup => 
                    `<li class="text-gray-600">${sup.name} - ${sup.dosage}</li>`
                ).join('');

                card.innerHTML = `
                    <h2 class="font-bold text-lg">${complex.name}</h2>
                    <ul class="list-disc list-inside mt-2">${supplementsHtml}</ul>
                `;
                complexesList.appendChild(card);
            });
        }
    };

    const addSupplementField = (name = '', dosage = '') => {
        const newField = document.createElement('div');
        newField.classList.add('flex', 'items-center', 'space-x-2');
        newField.innerHTML = `
            <input type="text" placeholder="Название препарата" class="w-2/3 px-3 py-2 border border-gray-300 rounded-md text-sm" value="${name}">
            <input type="text" placeholder="Дозировка" class="w-1/3 px-3 py-2 border border-gray-300 rounded-md text-sm" value="${dosage}">
            <button type="button" class="remove-supplement-btn text-red-500 font-bold">X</button>
        `;
        supplementsContainer.appendChild(newField);
        newField.querySelector('.remove-supplement-btn').addEventListener('click', () => newField.remove());
    };

    const openModal = () => {
        complexForm.reset();
        supplementsContainer.innerHTML = '';
        addSupplementField();
        saveBtn.disabled = false; // Включаем кнопку
        saveBtn.textContent = 'Сохранить'; // Возвращаем исходный текст
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        appElement.style.filter = 'blur(5px)';
    };

    const closeModal = () => {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        appElement.style.filter = 'none';
    };

    // --- Event Listeners ---
    openModalBtn.addEventListener('click', openModal);
    cancelBtn.addEventListener('click', closeModal);
    addSupplementBtn.addEventListener('click', () => addSupplementField());

    complexForm.addEventListener('submit', (event) => {
        event.preventDefault();

        // ИЗМЕНЕНИЕ: Даем пользователю обратную связь
        saveBtn.disabled = true;
        saveBtn.textContent = 'Сохранение...';
        
        const supplements = [];
        supplementsContainer.querySelectorAll('div').forEach(field => {
            const nameInput = field.querySelector('input[placeholder="Название препарата"]');
            const dosageInput = field.querySelector('input[placeholder="Дозировка"]');
            if (nameInput.value && dosageInput.value) {
                supplements.push({ name: nameInput.value, dosage: dosageInput.value });
            }
        });

        const complexData = {
            name: complexNameInput.value,
            supplements: supplements,
        };

        if (!complexData.name || complexData.supplements.length === 0) {
            tg.showAlert('Пожалуйста, укажите название и добавьте хотя бы один препарат.');
            saveBtn.disabled = false; // Включаем кнопку обратно
            saveBtn.textContent = 'Сохранить';
            return;
        }

        // Выводим в консоль то, что пытаемся отправить
        console.log("Отправка данных боту:", JSON.stringify(complexData));

        // Отправляем данные
        tg.sendData(JSON.stringify(complexData));

        // ИЗМЕНЕНИЕ: УБИРАЕМ tg.close()!
        // tg.close(); 
        // Теперь пользователь сам закроет окно, когда увидит подтверждение от бота в чате.
        // А мы через 1.5 секунды закроем модальное окно и вернем кнопку в исходное состояние.
        setTimeout(() => {
            closeModal();
        }, 1500);
    });

    // --- Initialization ---
    tg.ready();
    tg.expand();

    if (tg.initDataUnsafe && tg.initDataUnsafe.start_param) {
        try {
            const data = JSON.parse(tg.initDataUnsafe.start_param);
            loadingMessage.style.display = 'none';
            renderComplexes(data.complexes);
        } catch (e) {
            console.error("Не удалось обработать стартовые параметры:", e);
            loadingMessage.textContent = 'Ошибка загрузки данных.';
        }
    } else {
        loadingMessage.style.display = 'none';
        renderComplexes([]); // Показываем пустой список
    }
});
