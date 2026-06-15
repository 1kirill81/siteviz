document.addEventListener("DOMContentLoaded", () => {
    // 1. Имитация ответа API (JSON) для Прайса
    const servicesData = [
        {
            id: 1,
            name: "Архитектура и коррекция",
            description: "Построение формы, коррекция пинцетом/воском",
            price: "1000 ₽"
        },
        {
            id: 2,
            name: "Окрашивание (краска/хна)",
            description: "Подбор оттенка с учетом цветотипа и структуры волоса",
            price: "1200 ₽"
        },
        {
            id: 3,
            name: "Долговременная укладка",
            description: "Ламинирование, коррекция, уход",
            price: "2000 ₽"
        },
        {
            id: 4,
            name: "Комплекс 'Идеальные брови'",
            description: "Архитектура + ДУ + Окрашивание + SPA-уход",
            price: "3000 ₽"
        },
        {
            id: 5,
            name: "Алоха'",
            description: "Алоха описание",
            price: "3000 ₽"
        },
        {
            id: 6,
            name: "Реальная фотка",
            description: "описание",
            price: "3000 ₽"
        }
    ];

    // 2. Имитация ответа API (JSON) для Галереи
    // Используем плейсхолдеры. В будущем заменишь на URL с сервера.
    const galleryData = [
        {
            id: 1,
            imageUrl: "examples/b3bbc10d6159b7d6967cbbcf48540702.jpg",
            title: "Комплекс: ДУ + Окрашивание",
            description: "Материалы: Thuya (составы), Bronsun. Работа с асимметрией и жестким волосом."
        },
        {
            id: 2,
            imageUrl: "examples/e0552a0cf3a155d313243f26efac78e9.jpg",
            title: "Натуральное окрашивание",
            description: "Легкое тонирование краской Shik, коррекция воском Italwax."
        },
        {
            id: 3,
            imageUrl: "examples/e34b3df863291e0a81092b70d797613d.jpg",
            title: "Архитектура воском",
            description: "Создание чистой нижней линии, прореживание густых бровей."
        },
        {
            id: 4,
            imageUrl: "examples/i.webp",
            title: "Мужская коррекция",
            description: "Естественная чистка пушка вокруг формы, без эффекта 'выщипанных' бровей."
        },
        {
            id: 5,
            imageUrl: "examples/maxresdefault.jpg",
            title: "Идеальные брови",
            description: "Гармоничная форма и стойкий результат."
        },
        {
            id: 6,
            imageUrl: "examples/test.jpg",
            title: "Котик жостко качается",
            description: "Да да, реально качается"
        },
        {
            id: 7,
            imageUrl: "examples/test1.jpg",
            title: "Реальная фотка",
            description: "Дададада"
        }
    ];

    // 3. Рендер Прайс-листа (только для index.html)
    const servicesContainer = document.getElementById('services-container');
    if (servicesContainer) {
        servicesData.forEach(service => {
            const serviceEl = document.createElement('div');
            serviceEl.classList.add('service-item');
            serviceEl.innerHTML = `
                <div>
                    <div class="service-name">${service.name}</div>
                    <div class="service-desc">${service.description}</div>
                </div>
                <div class="service-price">${service.price}</div>
            `;
            servicesContainer.appendChild(serviceEl);
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
            // Передаем описание для модального окна Glightbox
            galleryEl.setAttribute('data-title', item.title);
            galleryEl.setAttribute('data-description', item.description);
            
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
});