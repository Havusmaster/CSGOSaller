TAILWIND = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSGO Saller</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        function openModal(id, name, desc, price, qty, floatVal, tradeBan, type, lang) {
            const t = {
                'ru': {
                    'float': 'Float',
                    'na': 'N/A',
                    'trade_ban': 'Trade Ban',
                    'yes': 'Да',
                    'no': 'Нет',
                    'type': 'Тип',
                    'weapon': 'Оружие',
                    'agent': 'Агент',
                    'product_link': 'Ссылка на товар',
                    'send_to_admin': 'Отправьте эту ссылку и вашу трейд-ссылку администратору в Telegram!',
                    'contact_admin': 'Написать админу',
                    'price': 'Цена',
                    'quantity': 'Количество'
                },
                'uz': {
                    'float': 'Float',
                    'na': 'Mavjud emas',
                    'trade_ban': 'Savdo taqiqlangan',
                    'yes': 'Ha',
                    'no': 'Yo‘q',
                    'type': 'Turi',
                    'weapon': 'Qurol',
                    'agent': 'Agent',
                    'product_link': 'Mahsulot havolasi',
                    'send_to_admin': 'Ushbu havolani va savdo havolangizni Telegram orqali administratorga yuboring!',
                    'contact_admin': 'Administratorga yozish',
                    'price': 'Narx',
                    'quantity': 'Soni'
                }
            };
            const translations = t[lang] || t['ru'];
            const floatText = floatVal !== null && type === 'weapon' ? `${translations['float']}: ${floatVal.toFixed(4)}` : type === 'welcome' ? '' : `${translations['float']}: ${translations['na']}`;
            const banText = tradeBan && type !== 'welcome' ? `${translations['trade_ban']}: ${translations['yes']}` : type !== 'welcome' ? `${translations['trade_ban']}: ${translations['no']}` : '';
            const typeText = type === 'weapon' ? `${translations['type']}: ${translations['weapon']}` : type === 'agent' ? `${translations['type']}: ${translations['agent']}` : '';
            const productLink = type !== 'welcome' ? `https://csgosaller-1.onrender.com/product/${id}` : '';
            const botUsername = '@UzSaler'; // Replace with actual bot username
            const modalContent = `
                <div class="bg-gray-800 p-6 rounded-lg max-w-md w-full animate-fade-in">
                    <h3 class="text-xl font-bold text-green-500 mb-4">${name}</h3>
                    <p class="text-gray-300 text-sm mb-2">${desc}</p>
                    ${type !== 'welcome' ? `
                    <p class="text-gray-300 text-sm mb-2">💰 ${translations['price']}: ${price}₽</p>
                    <p class="text-gray-300 text-sm mb-2">📦 ${translations['quantity']}: ${qty}</p>
                    <p class="text-gray-300 text-sm mb-2">${floatText}</p>
                    <p class="text-gray-300 text-sm mb-2">${banText}</p>
                    <p class="text-gray-300 text-sm mb-2">${typeText}</p>
                    <p class="text-gray-300 text-sm mb-3">🔗 ${translations['product_link']}: <a href="${productLink}" class="text-blue-500 hover:underline">${productLink}</a></p>
                    <p class="text-gray-300 text-sm mb-3">📋 ${translations['send_to_admin']}</p>
                    ` : ''}
                    <div class="flex flex-col gap-2">
                        ${type !== 'welcome' ? `<a href="https://t.me/${botUsername}" class="bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 text-center">${translations['contact_admin']}</a>` : ''}
                        <button onclick="document.getElementById('modal').style.display='none'" class="bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700">${lang === 'ru' ? 'Закрыть' : 'Yopish'}</button>
                    </div>
                </div>
            `;
            document.getElementById('modalContent').innerHTML = modalContent;
            document.getElementById('modal').style.display = 'flex';
        }

        function openLanguageModal() {
            const modalContent = `
                <div class="bg-gray-800 p-6 rounded-lg max-w-md w-full animate-fade-in">
                    <h3 class="text-xl font-bold text-orange-500 mb-4">${window.location.search.includes('lang=uz') ? 'Tilni tanlang' : 'Выберите язык'}</h3>
                    <p class="text-gray-300 text-sm mb-4">${window.location.search.includes('lang=uz') ? 'Iltimos, davom etish uchun tilni tanlang.' : 'Пожалуйста, выберите язык для продолжения.'}</p>
                    <div class="flex flex-col gap-2">
                        <button onclick="window.location.href='/?lang=ru&show_welcome=true'" class="bg-orange-500 text-white py-2 rounded-lg hover:bg-orange-600 transform hover:scale-105 transition duration-300">Русский</button>
                        <button onclick="window.location.href='/?lang=uz&show_welcome=true'" class="bg-orange-500 text-white py-2 rounded-lg hover:bg-orange-600 transform hover:scale-105 transition duration-300">O‘zbek</button>
                        <button onclick="document.getElementById('modal').style.display='none'" class="bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700">${window.location.search.includes('lang=uz') ? 'Yopish' : 'Закрыть'}</button>
                    </div>
                </div>
            `;
            document.getElementById('modalContent').innerHTML = modalContent;
            document.getElementById('modal').style.display = 'flex';
        }

        function searchItems(tableId) {
            const input = document.getElementById('searchInput').value.toLowerCase();
            const table = document.getElementById(tableId);
            const rows = table.getElementsByTagName('tr');
            for (let i = 1; i < rows.length; i++) {
                const cells = rows[i].getElementsByTagName('td');
                let match = false;
                for (let j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.toLowerCase().includes(input)) {
                        match = true;
                        break;
                    }
                }
                rows[i].style.display = match ? '' : 'none';
            }
        }

        function filterItemsByType(tableId) {
            const filter = document.getElementById('typeFilter').value;
            const table = document.getElementById(tableId);
            const rows = table.getElementsByTagName('tr');
            for (let i = 1; i < rows.length; i++) {
                const typeCell = rows[i].getElementsByTagName('td')[8];
                const typeText = typeCell.textContent.toLowerCase();
                rows[i].style.display = (filter === 'all' || (filter === 'weapon' && typeText.includes('оружие')) || (filter === 'agent' && typeText.includes('агент'))) ? '' : 'none';
            }
        }

        function toggleFloatField(selectId, floatDivId) {
            const select = document.getElementById(selectId);
            const floatDiv = document.getElementById(floatDivId);
            floatDiv.style.display = select.value === 'weapon' ? 'block' : 'none';
        }

        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('modal').style.display = 'none';
        });
    </script>
    <style>
        .card {
            transition: transform 0.2s;
        }
        .card:hover {
            transform: scale(1.03);
        }
        .btn {
            transition: background-color 0.2s, transform 0.2s;
        }
        .animate-fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body class="bg-gray-900 text-gray-300">
"""