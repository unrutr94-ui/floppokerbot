let currentUser = null;
let editingTournamentId = null;
let editingRatingId = null;
let editingPlayerId = null;
let currentTournamentId = null;

document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

function initApp() {
    console.log('🚀 Инициализация приложения');
    
    document.getElementById('director-auth-btn').addEventListener('click', () => showLoginForm('director'));
    document.getElementById('player-auth-btn').addEventListener('click', () => showLoginForm('player'));
    document.getElementById('director-login-btn').addEventListener('click', directorLogin);
    document.getElementById('player-login-btn').addEventListener('click', playerLogin);
    document.getElementById('back-to-auth').addEventListener('click', showAuthPage);
    document.getElementById('back-to-auth-2').addEventListener('click', showAuthPage);
    
    document.getElementById('logout-btn')?.addEventListener('click', logout);
    
    document.getElementById('back-to-main').addEventListener('click', () => showPage('main-page'));
    document.getElementById('back-to-main-2').addEventListener('click', () => showPage('main-page'));
    document.getElementById('back-to-main-3').addEventListener('click', () => showPage('main-page'));
    
    document.getElementById('save-tournament-btn').addEventListener('click', saveTournament);
    document.getElementById('cancel-tournament-btn').addEventListener('click', () => hideModal('tournament-modal'));
    
    document.getElementById('save-rating-btn').addEventListener('click', saveRating);
    document.getElementById('cancel-rating-btn').addEventListener('click', () => hideModal('rating-modal'));
    
    document.getElementById('save-player-btn').addEventListener('click', savePlayer);
    document.getElementById('cancel-player-btn').addEventListener('click', () => hideModal('player-modal'));
    
    document.getElementById('close-tables-btn').addEventListener('click', () => hideModal('tables-modal'));
    
    document.getElementById('add-player-btn').addEventListener('click', () => showPlayerModal());
}

function showAuthPage() {
    showPage('auth-page');
    document.getElementById('director-login-form').style.display = 'none';
    document.getElementById('player-login-form').style.display = 'none';
}

function showLoginForm(type) {
    if (type === 'director') {
        document.getElementById('director-login-form').style.display = 'block';
        document.getElementById('player-login-form').style.display = 'none';
    } else {
        document.getElementById('director-login-form').style.display = 'none';
        document.getElementById('player-login-form').style.display = 'block';
    }
}

async function directorLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        alert('Введите логин и пароль');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentUser = result.user;
            await loadUserProfile();
            showMainApp();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка соединения с сервером');
    }
}

async function playerLogin() {
    const telegramUsername = document.getElementById('telegram-username').value;
    
    if (!telegramUsername) {
        alert('Введите Telegram username');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/auth/telegram', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ telegram_username: telegramUsername })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentUser = result.user;
            await loadUserProfile();
            showMainApp();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка соединения с сервером');
    }
}

async function loadUserProfile() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`http://localhost:5000/api/user/profile/${currentUser.id}`);
        const result = await response.json();
        
        if (result.success) {
            currentUser.profile = result.profile;
        }
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
    }
}

function showMainApp() {
    showPage('main-page');
    
    const userInfoElement = document.getElementById('user-info-display');
    const roleElement = document.getElementById('user-role-display');
    const navButtonsElement = document.getElementById('main-nav-buttons');
    
    if (currentUser.role === 'director') {
        roleElement.textContent = '👑 Панель директора';
        userInfoElement.innerHTML = `
            <div>👤 ${currentUser.full_name}</div>
            <div>🔑 ${currentUser.username}</div>
        `;
        
        navButtonsElement.innerHTML = `
            <div class="nav-btn" id="tournaments-btn">
                🏆 Управление турнирами
            </div>
            
            <div class="nav-btn" id="players-btn">
                👥 Управление игроками
            </div>
            
            <div class="nav-btn" id="rating-btn">
                📊 Рейтинг игроков
            </div>

            <button id="logout-btn" class="btn btn-secondary" style="margin-top: 20px;">
                🚪 Выйти
            </button>
        `;
    } else {
        roleElement.textContent = '🎮 Панель игрока';
        
        const ratingInfo = currentUser.profile?.rating;
        
        userInfoElement.innerHTML = `
            <div>👤 ${currentUser.full_name}</div>
            <div>📱 ${currentUser.telegram_username}</div>
            ${ratingInfo ? `
                <div class="user-rating">
                    🏅 Рейтинг: ${ratingInfo.score} ${ratingInfo.position ? `(Место: ${ratingInfo.position})` : ''}
                </div>
            ` : `
                <div style="margin-top: 10px; opacity: 0.8;">Рейтинг не определён</div>
            `}
        `;
        
        navButtonsElement.innerHTML = `
            <div class="nav-btn" id="tournaments-btn">
                🏆 Турниры
            </div>
            
            <div class="nav-btn" id="rating-btn">
                📊 Рейтинг игроков
            </div>

            <button id="logout-btn" class="btn btn-secondary" style="margin-top: 20px;">
                🚪 Выйти
            </button>
        `;
    }
    
    document.getElementById('tournaments-btn').addEventListener('click', () => showPage('tournaments-page'));
    document.getElementById('rating-btn').addEventListener('click', () => showPage('rating-page'));
    if (currentUser.role === 'director') {
        document.getElementById('players-btn').addEventListener('click', () => showPage('players-page'));
    }
    document.getElementById('logout-btn').addEventListener('click', logout);
}

function logout() {
    currentUser = null;
    showAuthPage();
}

function showPage(pageId) {
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.remove('active');
    });
    
    document.getElementById(pageId).classList.add('active');
    
    if (currentUser) {
        switch(pageId) {
            case 'tournaments-page':
                loadTournaments();
                break;
            case 'rating-page':
                loadRating();
                break;
            case 'players-page':
                if (currentUser.role === 'director') {
                    loadPlayers();
                }
                break;
        }
    }
}

async function loadTournaments() {
    try {
        const titleElement = document.getElementById('tournaments-page-title');
        const contentElement = document.getElementById('tournaments-content');
        
        if (currentUser.role === 'director') {
            titleElement.textContent = '🏆 Управление турнирами';
            contentElement.innerHTML = `
                <button id="create-tournament-btn" class="btn btn-primary" style="width: 100%; margin-bottom: 20px;">
                    + Создать турнир
                </button>
            `;
            document.getElementById('create-tournament-btn').addEventListener('click', () => showTournamentModal());
        } else {
            titleElement.textContent = '🏆 Турниры';
            contentElement.innerHTML = '';
        }
        
        const response = await fetch('http://localhost:5000/api/tournaments');
        const tournaments = await response.json();
        displayTournaments(tournaments);
        
        // Добавляем обработчики для вкладок
        document.querySelectorAll('#tournament-tabs .tab').forEach(tab => {
            tab.addEventListener('click', function() {
                document.querySelectorAll('#tournament-tabs .tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                loadTournamentsWithStatus(this.dataset.status);
            });
        });
    } catch (error) {
        document.getElementById('tournaments-list').innerHTML = '<div class="empty-state">Ошибка загрузки турниров</div>';
    }
}

async function loadTournamentsWithStatus(status) {
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments?status=${status}`);
        const tournaments = await response.json();
        displayTournaments(tournaments);
    } catch (error) {
        document.getElementById('tournaments-list').innerHTML = '<div class="empty-state">Ошибка загрузки турниров</div>';
    }
}

function displayTournaments(tournaments) {
    const container = document.getElementById('tournaments-list');
    
    if (!tournaments || tournaments.length === 0) {
        container.innerHTML = '<div class="empty-state">Турниров нет</div>';
        return;
    }
    
    container.innerHTML = tournaments.map(t => {
        const statusBadge = getStatusBadge(t.status);
        return `
        <div class="item-card" onclick="showTournamentDetail(${t.id})">
            <div class="item-header">
                <div class="item-title">${t.name}</div>
                <div class="status-badge ${statusBadge.class}">${statusBadge.text}</div>
            </div>
            
            <div class="item-details">
                <div class="detail-group">
                    <div class="detail-label">Аренда</div>
                    <div class="detail-value">${t.rent_cost} руб / ${t.rent_chips} фишек</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Повтор</div>
                    <div class="detail-value">${t.rebuy_cost} руб / ${t.rebuy_chips} фишек</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Аддон</div>
                    <div class="detail-value">${t.addon_cost} руб / ${t.addon_chips} фишек</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Начало</div>
                    <div class="detail-value">${new Date(t.start_time).toLocaleString('ru-RU')}</div>
                </div>
                <div class="detail-group">
                    <div class="detail-label">Статус</div>
                    <div class="detail-value">${statusBadge.text}</div>
                </div>
            </div>
            
            ${currentUser.role === 'director' ? `
            <div class="item-actions">
                <button class="btn btn-small btn-primary" onclick="event.stopPropagation(); editTournament(${t.id})">✏️ Редактировать</button>
                <button class="btn btn-small btn-secondary" onclick="event.stopPropagation(); deleteTournament(${t.id})">🗑️ Удалить</button>
            </div>
            ` : ''}
        </div>
    `}).join('');
}

function getStatusBadge(status) {
    switch(status) {
        case 'registration':
            return { class: 'status-registration', text: 'Регистрация' };
        case 'late_registration':
            return { class: 'status-late_registration', text: 'Поздняя регистрация' };
        case 'active':
            return { class: 'status-active', text: 'Идет турнир' };
        case 'active_no_late_reg':
            return { class: 'status-active_no_late_reg', text: 'Регистрация закрыта' };
        case 'completed':
            return { class: 'status-completed', text: 'Завершен' };
        default:
            return { class: 'status-registration', text: status };
    }
}

async function showTournamentDetail(tournamentId) {
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}`);
        const tournament = await response.json();
        
        if (tournament.success === false) {
            alert('Ошибка: ' + tournament.message);
            return;
        }
        
        currentTournamentId = tournamentId;
        document.getElementById('tournament-detail-title').textContent = tournament.name;
        
        const actionsElement = document.getElementById('tournament-detail-actions');
        let actionsHTML = '';

        // Проверяем, зарегистрирован ли пользователь
        const isRegistered = tournament.players && tournament.players.some(player => player.user_id === currentUser.id);
        
        // Кнопка регистрации для всех пользователей (игроков и директоров)
        // Показываем только если пользователь еще не зарегистрирован и турнир в стадии регистрации
        if ((tournament.status === 'registration' || tournament.status === 'late_registration') && !isRegistered) {
            actionsHTML += `<button id="register-tournament-btn" class="btn btn-success">Зарегистрироваться</button>`;
        }
        
        // Кнопка показа столов для всех пользователей
        actionsHTML += `<button id="show-tables-btn" class="btn btn-info">📋 Показать столы</button>`;
        
        if (currentUser.role === 'director') {
            // Кнопки управления для директора
            if (tournament.status === 'registration') {
                actionsHTML += `<button id="start-tournament-btn" class="btn btn-primary">▶️ Начать турнир</button>`;
            } else if (tournament.status === 'late_registration' || tournament.status === 'active') {
                actionsHTML += `<button id="close-late-reg-btn" class="btn btn-warning">🚫 Закрыть регистрацию</button>`;
                actionsHTML += `<button id="complete-tournament-btn" class="btn btn-error">🏁 Завершить турнир</button>`;
            } else if (tournament.status === 'active_no_late_reg') {
                actionsHTML += `<button id="complete-tournament-btn" class="btn btn-error">🏁 Завершить турнир</button>`;
            }
            
            actionsHTML += `<button id="create-tables-btn" class="btn btn-secondary">🎯 Создать столы</button>`;
        }
        
        actionsHTML += `<button id="close-tournament-detail-btn" class="btn btn-secondary">Закрыть</button>`;
        
        actionsElement.innerHTML = actionsHTML;
        
        // Добавляем обработчики событий
        if (document.getElementById('register-tournament-btn')) {
            document.getElementById('register-tournament-btn').addEventListener('click', (event) => {
                event.stopPropagation();
                registerForCurrentTournament();
            });
        }
        
        // Обработчики для кнопок столов (доступны всем)
        document.getElementById('show-tables-btn').addEventListener('click', (event) => {
            event.stopPropagation();
            showTournamentTables(tournamentId);
        });
        
        if (currentUser.role === 'director') {
            if (document.getElementById('start-tournament-btn')) {
                document.getElementById('start-tournament-btn').addEventListener('click', (event) => {
                    event.stopPropagation();
                    startTournament(tournamentId);
                });
            }
            if (document.getElementById('close-late-reg-btn')) {
                document.getElementById('close-late-reg-btn').addEventListener('click', (event) => {
                    event.stopPropagation();
                    closeLateRegistration(tournamentId);
                });
            }
            if (document.getElementById('complete-tournament-btn')) {
                document.getElementById('complete-tournament-btn').addEventListener('click', (event) => {
                    event.stopPropagation();
                    completeTournament(tournamentId);
                });
            }
            
            document.getElementById('create-tables-btn').addEventListener('click', (event) => {
                event.stopPropagation();
                createTournamentTables(tournamentId);
            });
        }
        
        document.getElementById('close-tournament-detail-btn').addEventListener('click', (event) => {
            event.stopPropagation();
            hideModal('tournament-detail-modal');
        });
        
        // Отображаем детали турнира с игроками и их фишками
        displayTournamentDetails(tournament);
        
        showModal('tournament-detail-modal');
        
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        alert('Ошибка загрузки информации о турнире: ' + error.message);
    }
}

function displayTournamentDetails(tournament) {
    const contentElement = document.getElementById('tournament-detail-content');
    
    // Сортируем игроков по фишкам если турнир активен
    let sortedPlayers = tournament.players || [];
    if (tournament.status === 'active' || tournament.status === 'late_registration' || tournament.status === 'active_no_late_reg') {
        sortedPlayers = [...sortedPlayers].sort((a, b) => b.chips - a.chips);
    }
    
    contentElement.innerHTML = `
        <div class="tournament-detail-layout">
            <div class="tournament-detail-section">
                <h4>📊 Основная информация</h4>
                <div class="detail-item">
                    <span class="detail-label">Статус:</span>
                    <span class="detail-value">${getStatusBadge(tournament.status).text}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Аренда:</span>
                    <span class="detail-value">${tournament.rent_cost} рублей</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Стартовые фишки:</span>
                    <span class="detail-value">${tournament.rent_chips.toLocaleString('ru-RU')}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Время уровней:</span>
                    <span class="detail-value">${tournament.level_time || 15} минут</span>
                </div>
            </div>
            
            <div class="tournament-detail-section">
                <h4>📈 Статистика турнира</h4>
                <div class="detail-item">
                    <span class="detail-label">Участников:</span>
                    <span class="detail-value">${tournament.registered_players} игроков</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Общий банк:</span>
                    <span class="detail-value">${tournament.total_chips.toLocaleString('ru-RU')} фишек</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Начало:</span>
                    <span class="detail-value">${new Date(tournament.start_time).toLocaleString('ru-RU')}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Окончание регистрации:</span>
                    <span class="detail-value">${new Date(tournament.late_reg_end_time).toLocaleString('ru-RU')}</span>
                </div>
            </div>
        </div>
        
        <div class="tournament-detail-section">
            <h4>🎮 Зарегистрированные игроки ${(tournament.status === 'active' || tournament.status === 'late_registration' || tournament.status === 'active_no_late_reg') ? '(сортировка по фишкам)' : ''}</h4>
            ${sortedPlayers.length > 0 ? 
                sortedPlayers.map(player => `
                    <div class="player-chips-item">
                        <div class="player-chips-info">
                            <div class="player-chips-name">${player.game_nickname} ${player.user_id === currentUser.id ? ' (Вы)' : ''}</div>
                            <div class="player-chips-rating">Рейтинг: ${player.rating}</div>
                        </div>
                        <div class="player-chips-controls">
                            <span class="chips-display">${player.chips.toLocaleString('ru-RU')} фишек</span>
                            ${currentUser.role === 'director' && (tournament.status === 'active' || tournament.status === 'late_registration' || tournament.status === 'active_no_late_reg') ? `
                                <input type="number" class="chips-input" value="${player.chips}" 
                                    onchange="updatePlayerChips(${tournament.id}, ${player.user_id}, this.value)"
                                    placeholder="Фишки">
                            ` : ''}
                        </div>
                    </div>
                `).join('') : 
                '<div class="empty-state" style="padding: 20px; text-align: center;">Нет зарегистрированных игроков</div>'
            }
        </div>
    `;
}

async function updatePlayerChips(tournamentId, playerUserId, chips) {
    if (!chips || chips < 0) {
        alert('Введите корректное количество фишек');
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}/update-chips`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                player_user_id: playerUserId,
                chips: parseInt(chips)
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Обновляем отображение без перезагрузки страницы
            showTournamentDetail(tournamentId);
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка обновления фишек');
    }
}

async function registerForCurrentTournament() {
    if (!currentTournamentId) return;
    
    if (!confirm('Вы уверены, что хотите зарегистрироваться на турнир?')) {
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                tournament_id: currentTournamentId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Регистрация успешна');
            hideModal('tournament-detail-modal');
            loadTournaments();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка регистрации');
    }
}

async function startTournament(tournamentId) {
    if (!confirm('Начать турнир? После начала будет доступна поздняя регистрация до указанного времени.')) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            hideModal('tournament-detail-modal');
            loadTournaments();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка запуска турнира');
    }
}

async function closeLateRegistration(tournamentId) {
    if (!confirm('Закрыть позднюю регистрацию? После этого новые игроки не смогут присоединиться к турниру.')) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}/close-late-reg`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            hideModal('tournament-detail-modal');
            loadTournaments();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка закрытия регистрации');
    }
}

async function completeTournament(tournamentId) {
    if (!confirm('Завершить турнир? Это действие нельзя отменить.')) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            hideModal('tournament-detail-modal');
            loadTournaments();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка завершения турнира');
    }
}

async function createTournamentTables(tournamentId) {
    if (!confirm('Создать столы для турнира? Игроки будут автоматически распределены.')) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}/create-tables`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            // Показываем столы сразу, не переключая страницы
            await showTournamentTables(tournamentId);
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка создания столов');
    }
}

async function showTournamentTables(tournamentId) {
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}/tables`);
        const result = await response.json();
        
        // Проверяем, если ответ содержит success: false
        if (result.success === false) {
            alert('Ошибка: ' + result.message);
            return;
        }
        
        const tables = result;
        
        const tablesContent = document.getElementById('tables-content');
        
        if (!tables || tables.length === 0) {
            tablesContent.innerHTML = '<div class="empty-state">Столы не созданы</div>';
        } else {
            tablesContent.innerHTML = `
                <div class="tables-grid">
                    ${tables.map(table => `
                        <div class="table-card">
                            <div class="table-header">
                                <h4>Стол ${table.table_number}</h4>
                                <span class="table-info">${table.current_players}/${table.max_players} игроков</span>
                            </div>
                            <div class="table-players">
                                ${table.players && table.players.length > 0 ? 
                                    table.players.map(player => `
                                        <div class="player-seat">
                                            <span class="seat-number">${player.seat_number}</span>
                                            <span class="player-name">${player.full_name}</span>
                                            <span class="player-rating">${player.rating}</span>
                                            <span class="player-chips">${player.chips ? player.chips.toLocaleString('ru-RU') : '0'} фишек</span>
                                        </div>
                                    `).join('') : 
                                    '<div class="empty-state">Нет игроков за столом</div>'
                                }
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Показываем модальное окно столов поверх текущего
        showModal('tables-modal');
        
    } catch (error) {
        console.error('Ошибка загрузки столов:', error);
        alert('Ошибка загрузки столов: ' + error.message);
    }
}

function showTournamentModal() {
    editingTournamentId = null;
    document.getElementById('tournament-modal-title').textContent = 'Создать турнир';
    document.getElementById('tournament-name').value = '';
    document.getElementById('tournament-rent-cost').value = '';
    document.getElementById('tournament-rent-chips').value = '';
    document.getElementById('tournament-rebuy-cost').value = '0';
    document.getElementById('tournament-rebuy-chips').value = '0';
    document.getElementById('tournament-addon-cost').value = '0';
    document.getElementById('tournament-addon-chips').value = '0';
    document.getElementById('tournament-level-time').value = '15';
    document.getElementById('tournament-time').value = '';
    document.getElementById('tournament-late-reg-time').value = '';
    showModal('tournament-modal');
}

async function editTournament(tournamentId) {
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}`);
        const tournament = await response.json();
        
        if (tournament.success === false) {
            alert('Ошибка: ' + tournament.message);
            return;
        }
        
        editingTournamentId = tournamentId;
        document.getElementById('tournament-modal-title').textContent = 'Редактировать турнир';
        document.getElementById('tournament-name').value = tournament.name;
        document.getElementById('tournament-rent-cost').value = tournament.rent_cost;
        document.getElementById('tournament-rent-chips').value = tournament.rent_chips;
        document.getElementById('tournament-rebuy-cost').value = tournament.rebuy_cost;
        document.getElementById('tournament-rebuy-chips').value = tournament.rebuy_chips;
        document.getElementById('tournament-addon-cost').value = tournament.addon_cost;
        document.getElementById('tournament-addon-chips').value = tournament.addon_chips;
        document.getElementById('tournament-level-time').value = tournament.level_time || 15;
        document.getElementById('tournament-time').value = tournament.start_time.slice(0, 16);
        document.getElementById('tournament-late-reg-time').value = tournament.late_reg_end_time.slice(0, 16);
        
        showModal('tournament-modal');
    } catch (error) {
        alert('Ошибка загрузки турнира');
    }
}

async function deleteTournament(tournamentId) {
    if (!confirm('Вы уверены, что хотите удалить турнир?')) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/tournaments/${tournamentId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Турнир удалён');
            loadTournaments();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка удаления турнира');
    }
}

async function saveTournament() {
    const name = document.getElementById('tournament-name').value;
    const rentCost = document.getElementById('tournament-rent-cost').value;
    const rentChips = document.getElementById('tournament-rent-chips').value;
    const rebuyCost = document.getElementById('tournament-rebuy-cost').value;
    const rebuyChips = document.getElementById('tournament-rebuy-chips').value;
    const addonCost = document.getElementById('tournament-addon-cost').value;
    const addonChips = document.getElementById('tournament-addon-chips').value;
    const levelTime = document.getElementById('tournament-level-time').value;
    const startTime = document.getElementById('tournament-time').value;
    const lateRegTime = document.getElementById('tournament-late-reg-time').value;
    
    if (!name || !rentCost || !rentChips || !startTime || !lateRegTime) {
        alert('Заполните основные поля: название, аренда (стоимость и фишки), время начала и окончания регистрации');
        return;
    }
    
    const tournamentData = {
        user_id: currentUser.id,
        name,
        rent_cost: parseInt(rentCost),
        rent_chips: parseInt(rentChips),
        rebuy_cost: parseInt(rebuyCost) || 0,
        rebuy_chips: parseInt(rebuyChips) || 0,
        addon_cost: parseInt(addonCost) || 0,
        addon_chips: parseInt(addonChips) || 0,
        level_time: parseInt(levelTime) || 15,
        start_time: startTime,
        late_reg_end_time: lateRegTime
    };
    
    try {
        const url = editingTournamentId 
            ? `http://localhost:5000/api/tournaments/${editingTournamentId}`
            : 'http://localhost:5000/api/tournaments';
            
        const method = editingTournamentId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tournamentData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(editingTournamentId ? 'Турнир обновлён' : 'Турнир создан');
            hideModal('tournament-modal');
            loadTournaments();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка сохранения турнира');
    }
}

async function loadRating() {
    try {
        const contentElement = document.getElementById('rating-content');
        
        if (currentUser.role === 'director') {
            contentElement.innerHTML = `
                <button id="add-rating-btn" class="btn btn-primary" style="width: 100%; margin-bottom: 20px;">
                    + Добавить игрока в рейтинг
                </button>
            `;
            document.getElementById('add-rating-btn').addEventListener('click', () => showRatingModal());
        } else {
            contentElement.innerHTML = '';
        }
        
        const response = await fetch('http://localhost:5000/api/rating');
        const rating = await response.json();
        displayRating(rating);
    } catch (error) {
        document.getElementById('rating-list').innerHTML = '<div class="empty-state">Ошибка загрузки рейтинга</div>';
    }
}

function displayRating(rating) {
    const container = document.getElementById('rating-list');
    
    if (!rating || rating.length === 0) {
        container.innerHTML = '<div class="empty-state">Рейтинг пуст</div>';
        return;
    }
    
    container.innerHTML = rating.map((r, index) => {
        let medal = '';
        if (index === 0) medal = '🥇 ';
        else if (index === 1) medal = '🥈 ';
        else if (index === 2) medal = '🥉 ';
        
        return `
            <div class="rating-item">
                <div class="rating-position">${medal}${index + 1}</div>
                <div class="rating-info">
                    <div class="rating-name">${r.player_name}</div>
                    <div class="rating-username">@${r.telegram_username}</div>
                </div>
                <div class="rating-score">${r.score}</div>
                ${currentUser.role === 'director' ? `
                <div class="item-actions">
                    <button class="btn btn-small btn-primary" onclick="editRating(${r.id})">✏️</button>
                    <button class="btn btn-small btn-secondary" onclick="deleteRating(${r.id})">🗑️</button>
                </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function showRatingModal() {
    editingRatingId = null;
    document.getElementById('rating-modal-title').textContent = 'Добавить в рейтинг';
    document.getElementById('rating-player-name').value = '';
    document.getElementById('rating-telegram-username').value = '';
    document.getElementById('rating-score').value = '1000';
    showModal('rating-modal');
}

async function editRating(ratingId) {
    try {
        const response = await fetch('http://localhost:5000/api/rating');
        const rating = await response.json();
        const ratingItem = rating.find(r => r.id === ratingId);
        
        if (!ratingItem) {
            alert('Рейтинг не найден');
            return;
        }
        
        editingRatingId = ratingId;
        document.getElementById('rating-modal-title').textContent = 'Редактировать рейтинг';
        document.getElementById('rating-player-name').value = ratingItem.player_name;
        document.getElementById('rating-telegram-username').value = ratingItem.telegram_username;
        document.getElementById('rating-score').value = ratingItem.score;
        
        showModal('rating-modal');
    } catch (error) {
        alert('Ошибка загрузки рейтинга');
    }
}

async function deleteRating(ratingId) {
    if (!confirm('Вы уверены, что хотите удалить игрока из рейтинга?')) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/rating/${ratingId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Игрок удалён из рейтинга');
            loadRating();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка удаления рейтинга');
    }
}

async function saveRating() {
    const playerName = document.getElementById('rating-player-name').value;
    const telegramUsername = document.getElementById('rating-telegram-username').value;
    const score = document.getElementById('rating-score').value;
    
    if (!playerName || !telegramUsername) {
        alert('Имя игрока и Telegram username обязательны');
        return;
    }
    
    const ratingData = {
        user_id: currentUser.id,
        player_name: playerName,
        telegram_username: telegramUsername.replace('@', ''),
        score: parseInt(score) || 1000
    };
    
    try {
        const url = editingRatingId 
            ? `http://localhost:5000/api/rating/${editingRatingId}`
            : 'http://localhost:5000/api/rating';
            
        const method = editingRatingId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ratingData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(editingRatingId ? 'Рейтинг обновлён' : 'Игрок добавлен в рейтинг');
            hideModal('rating-modal');
            loadRating();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка сохранения рейтинга');
    }
}

async function loadPlayers() {
    try {
        const response = await fetch(`http://localhost:5000/api/admin/players?user_id=${currentUser.id}`);
        const players = await response.json();
        displayPlayers(players);
    } catch (error) {
        document.getElementById('players-list').innerHTML = '<div class="empty-state">Ошибка загрузки игроков</div>';
    }
}

function displayPlayers(players) {
    const container = document.getElementById('players-list');
    
    if (!players || players.length === 0) {
        container.innerHTML = '<div class="empty-state">Игроков нет</div>';
        return;
    }
    
    container.innerHTML = players.map(player => `
        <div class="player-item">
            <div class="player-info">
                <div class="player-name">${player.full_name}</div>
                <div class="player-username">@${player.telegram_username}</div>
                <div class="player-rating">Рейтинг: ${player.rating_score}</div>
            </div>
            <div class="item-actions">
                <button class="btn btn-small btn-secondary" onclick="deletePlayer(${player.id})">🗑️ Удалить</button>
            </div>
        </div>
    `).join('');
}

function showPlayerModal() {
    editingPlayerId = null;
    document.getElementById('player-modal-title').textContent = 'Добавить игрока';
    document.getElementById('player-telegram-username').value = '';
    document.getElementById('player-full-name').value = '';
    showModal('player-modal');
}

async function deletePlayer(playerId) {
    if (!confirm('Вы уверены, что хотите удалить игрока?')) {
        return;
    }
    
    try {
        const response = await fetch(`http://localhost:5000/api/admin/players/${playerId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Игрок удалён');
            loadPlayers();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка удаления игрока');
    }
}

async function savePlayer() {
    const telegramUsername = document.getElementById('player-telegram-username').value;
    const fullName = document.getElementById('player-full-name').value;
    
    if (!telegramUsername || !fullName) {
        alert('Telegram username и полное имя обязательны');
        return;
    }
    
    const playerData = {
        user_id: currentUser.id,
        telegram_username: telegramUsername.replace('@', ''),
        full_name: fullName
    };
    
    try {
        const response = await fetch('http://localhost:5000/api/admin/create_player', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(playerData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Игрок создан');
            hideModal('player-modal');
            loadPlayers();
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка создания игрока');
    }
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Сбрасываем только при закрытии модального окна деталей турнира
    if (modalId === 'tournament-detail-modal') {
        currentTournamentId = null;
    }
    
    // Очищаем другие ID редактирования
    if (modalId === 'tournament-modal') {
        editingTournamentId = null;
    }
    if (modalId === 'rating-modal') {
        editingRatingId = null;
    }
    if (modalId === 'player-modal') {
        editingPlayerId = null;
    }
}