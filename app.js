document.addEventListener("DOMContentLoaded", () => {
    // 1. Имитация ответа API (JSON) для Прайса
    const servicesData = [
        {
            id: 1,
            name: "Архитектура и коррекция",
            description: "Построение формы, коррекция пинцетом/воском",
            fullDescription: "В услугу входит детальный разбор формы лица, подбор индивидуальной архитектуры бровей. Мы удаляем лишние волоски при помощи профессионального пинцета и гипоаллергенного воска, создавая четкие и чистые линии.",
            price: "1000 ₽"
        },
        {
            id: 2,
            name: "Окрашивание (краска/хна)",
            description: "Подбор оттенка с учетом цветотипа и структуры волоса",
            fullDescription: "Используем только премиальные красители. Окрашивание позволяет сделать брови более выразительными, заполнить пустоты и добиться нужного оттенка, который будет гармонировать с вашим цветом волос.",
            price: "1200 ₽"
        },
        {
            id: 3,
            name: "Долговременная укладка",
            description: "Ламинирование, коррекция, уход",
            fullDescription: "Идеальное решение для непослушных, жестких или растущих вниз волосков. Составы делают волос мягким и податливым, позволяя уложить брови в нужную форму. Эффект сохраняется до 6-8 недель.",
            price: "2000 ₽"
        },
        {
            id: 4,
            name: "Комплекс 'Идеальные брови'",
            description: "Архитектура + ДУ + Окрашивание + SPA-уход",
            fullDescription: "Максимальное преображение вашего взгляда. Включает в себя все этапы: от создания формы до глубокого восстановления волосков специальными составами. Полный цикл ухода за один визит.",
            price: "3000 ₽"
        },
        {
            id: 5,
            name: "Удаление нежелательных волос",
            description: "Верхняя губа / подбородок / бакенбарды",
            fullDescription: "Быстрое и бережное удаление пушковых и жестких волос на лице при помощи деликатного воска. Минимальное раздражение и гладкая кожа надолго.",
            price: "от 300 ₽"
        },
        {
            id: 6, 
            name: "Test",
            description: "Test desc",
            fullDescription: "test ful",
            price: "500 ₽"
        }

    ];

    // 2. Имитация ответа API (JSON) для Галереи
    // Используем плейсхолдеры. В будущем заменишь на URL с сервера.
    const galleryData = [
        {
            id: 1,
            imageUrl: "examples/photo1.jpg",
            title: "Пусто",
            description: "Пусто"
        },
        {
            id: 2,
            imageUrl: "examples/photo2.jpg",
            title: "Пусто",
            description: "Пусто"
        },

    ];

    // 3. Рендер Прайс-листа (только для index.html)
    const servicesContainer = document.getElementById('services-container');
    if (servicesContainer) {
        servicesData.forEach(service => {
            const serviceEl = document.createElement('div');
            serviceEl.classList.add('service-item');
            serviceEl.innerHTML = `
                <div class="service-main">
                    <div class="service-info">
                        <div class="service-name-row">
                            <span class="service-name">${service.name}</span>
                            <span class="service-arrow">▼</span>
                        </div>
                        <div class="service-desc">${service.description}</div>
                    </div>
                    <div class="service-price">${service.price}</div>
                </div>
                <div class="service-details">
                    <div class="service-details-content">
                        ${service.fullDescription}
                    </div>
                </div>
            `;
            
            serviceEl.addEventListener('click', () => {
                const isActive = serviceEl.classList.contains('active');
                
                // Закрываем все остальные (если нужно)
                // document.querySelectorAll('.service-item').forEach(el => el.classList.remove('active'));
                
                if (!isActive) {
                    serviceEl.classList.add('active');
                } else {
                    serviceEl.classList.remove('active');
                }
            });
            
            servicesContainer.appendChild(serviceEl);
        });
    }

    // --- Логика формы обратной связи ---
    const feedbackForm = document.getElementById('feedback-form');
    const checkboxesContainer = document.getElementById('services-checkboxes');
    const totalPriceElement = document.getElementById('total-price');

    if (feedbackForm && checkboxesContainer) {
        // 1. Динамическое заполнение списка услуг чекбоксами
        servicesData.forEach(service => {
            const checkboxWrapper = document.createElement('div');
            checkboxWrapper.classList.add('checkbox-item');
            
            // Извлекаем числовое значение цены для расчетов
            const priceValue = parseInt(service.price.replace(/[^0-9]/g, '')) || 0;

            checkboxWrapper.innerHTML = `
                <label class="custom-checkbox">
                    <input type="checkbox" name="service" value="${service.name}" data-price="${priceValue}">
                    <span class="checkmark"></span>
                    <span class="checkbox-label">${service.name} — ${service.price}</span>
                </label>
            `;
            checkboxesContainer.appendChild(checkboxWrapper);
        });

        // Функция обновления итоговой стоимости
        const updateTotalPrice = () => {
            let total = 0;
            const checkedBoxes = checkboxesContainer.querySelectorAll('input[type="checkbox"]:checked');
            checkedBoxes.forEach(cb => {
                total += parseInt(cb.getAttribute('data-price'));
            });
            totalPriceElement.textContent = `${total} ₽`;
        };

        // Слушатель изменений на контейнере чекбоксов
        checkboxesContainer.addEventListener('change', updateTotalPrice);

        // 2. Обработка отправки формы
        feedbackForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const submitBtn = feedbackForm.querySelector('.submit-btn');
            const originalBtnText = submitBtn.textContent;
            const backendUrl = 'http://localhost:8000/api/booking';
            // const backendUrl = '/api/booking';

            // Проверка, выбрана ли хоть одна услуга
            const selectedServices = Array.from(checkboxesContainer.querySelectorAll('input[type="checkbox"]:checked'))
                                          .map(cb => cb.value);
            
            if (selectedServices.length === 0) {
                alert('Пожалуйста, выберите хотя бы одну услугу.');
                return;
            }

            // Блокировка кнопки
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';

            // Собираем данные
            const formData = new FormData(feedbackForm);
            // FormData автоматически соберет все выбранные чекбоксы с именем "service"
            // Но для GAS иногда удобнее передать их одной строкой
            formData.set('services', selectedServices.join(', '));
            formData.set('total_price', totalPriceElement.textContent);

            fetch(backendUrl, {
                method: 'POST',
                body: formData
            })
            .then(() => {
                alert('Спасибо! Ваша заявка принята. Я свяжусь с вами в ближайшее время.');
                feedbackForm.reset();
                updateTotalPrice(); // Сброс цены до 0
            })
            .catch(error => {
                console.error('Ошибка при отправке:', error);
                alert('Произошла ошибка при отправке. Пожалуйста, попробуйте позже.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            });
        });
    }

    // 4. Рендер Галереи (только для gallery.html)
    const galleryContainer = document.getElementById('gallery-container');
    if (galleryContainer) {
        galleryData.forEach(item => {
            const galleryEl = document.createElement('a');
            // href нужен для библиотеки Glightbox
            galleryEl.href = item.imageUrl;
            galleryEl.classList.add('gallery-item', 'glightbox');
            // Передаем описание для модального окна Glightbox через единый атрибут
            galleryEl.setAttribute('data-glightbox', `title: ${item.title}; description: ${item.description}`);
            
            galleryEl.innerHTML = `
                <img src="${item.imageUrl}" alt="${item.title}" loading="lazy">
                <div class="gallery-overlay">
                    <div class="service-name">${item.title}</div>
                    <div class="service-desc">${item.description}</div>
                </div>
            `;
            galleryContainer.appendChild(galleryEl);
        });

        // Инициализация библиотеки GLightbox ПОСЛЕ рендера элементов
        const lightbox = GLightbox({
            selector: '.glightbox',
            touchNavigation: true,
            loop: true,
            zoomable: true
        });
    }

    // --- Логика модального окна "Сайт в разработке" ---
    const devModal = document.getElementById('dev-modal');
    const devModalOk = document.getElementById('dev-modal-ok');

    if (devModal && devModalOk) {
        // Проверяем, было ли окно уже закрыто ранее
        const isDismissed = localStorage.getItem('dev-banner-dismissed');

        if (isDismissed === 'true') {
            // Если закрыто, скрываем сразу без анимации
            devModal.classList.add('hidden');
            devModal.style.transition = 'none'; 
        }

        // Обработчик клика на кнопку "Принять"
        devModalOk.addEventListener('click', () => {
            devModal.classList.add('hidden');
            localStorage.setItem('dev-banner-dismissed', 'true');
        });
    }
});

/* --- Supernatural Easter Egg --- */
(function() {
    const impalaImgUrl = 'car.png'; 
    const duration = 2000; 

    const style = document.createElement('style');
    style.textContent = `
        .impala-easter-egg {
            position: fixed;
            bottom: 12vh;
            left: -450px;
            width: 350px;
            height: auto;
            z-index: 100000;
            pointer-events: none;
            transition: transform ${duration}ms linear;
            will-change: transform;
        }
        @media (max-width: 600px) {
            .impala-easter-egg {
                width: 200px;
                bottom: 8vh;
                left: -250px;
            }
        }
    `;
    document.head.appendChild(style);

    let isLaunching = false;

    function launchImpala() {
        if (isLaunching) return;
        isLaunching = true;

        const car = document.createElement('img');
        car.src = impalaImgUrl;
        car.className = 'impala-easter-egg';
        car.alt = 'Supernatural Impala 67';
        
        document.body.appendChild(car);

        // Первый кадр: даем браузеру отрисовать элемент в начальной точке
        requestAnimationFrame(() => {
            const carWidth = car.offsetWidth || 350;
            const distance = window.innerWidth + carWidth + 200;
            
            // Второй кадр: запускаем CSS-переход со смещением
            requestAnimationFrame(() => {
                car.style.transform = `translateX(${distance}px)`;
            });
        });

        setTimeout(() => {
            car.remove();
            isLaunching = false;
        }, duration + 500);
    }

    // Используем делегирование, но с проверкой типа события для мобилок
    const handleTrigger = (event) => {
        const flipContainer = event.target.closest('.photo-flip-container');
        if (flipContainer) {
            launchImpala();
            
            if (!flipContainer.classList.contains('flipped')) {
                flipContainer.classList.add('flipped');
                setTimeout(() => {
                    flipContainer.classList.remove('flipped');
                }, 1000);
            }
        }
    };

    // Слушаем click — это работает и для клика, и для тача максимально быстро
    document.addEventListener('click', handleTrigger);
})();




