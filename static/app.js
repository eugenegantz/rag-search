const API_BASE = '';

const ALLOWED_EXTENSIONS = ['.docx', '.pdf', '.txt', '.md'];

function validateFilePath(path) {
    const ext = path.toLowerCase().slice(path.lastIndexOf('.'));
    return ALLOWED_EXTENSIONS.includes(ext);
}

function getFileExtension(path) {
    return path.toLowerCase().slice(path.lastIndexOf('.'));
}

function showStatus(elementId, message, type = 'info') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = message;
    el.className = 'b-status b-status_' + type;
    el.style.display = 'block';
}

function hideStatus(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.style.display = 'none';
}

function setLoading(buttonId, isLoading) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.disabled = isLoading;
    if (isLoading) {
        btn.innerHTML = '<span class="b-spinner"></span> Обработка...';
    } else {
        btn.textContent = btn.dataset.originalText || 'Отправить';
    }
}

async function searchDocuments() {
    const queryInput = document.getElementById('query');
    // const topKInput = document.getElementById('top_k');
    const resultsDiv = document.getElementById('results');
    
    const query = queryInput.value.trim();
    // const topK = parseInt(topKInput.value) || 5;
    
    if (!query) {
        showStatus('search-status', 'Введите поисковый запрос', 'error');
        return;
    }
    
    hideStatus('search-status');
    setLoading('search-btn', true);
    
    try {
        const response = await fetch(`${API_BASE}/api/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query,
                // top_k: topK
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showStatus('search-status', data.error, 'error');
            resultsDiv.innerHTML = '';
        } else {
            showStatus('search-status', `Найдено результатов: ${data.results?.length || 0}`, 'success');
            renderResults(data.results || []);
        }
    } catch (err) {
        showStatus('search-status', 'Ошибка соединения с сервером', 'error');
        resultsDiv.innerHTML = '';
    } finally {
        setLoading('search-btn', false);
    }
}

function renderResults(results) {
    const resultsDiv = document.getElementById('results');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="b-empty">Ничего не найдено</div>';
        return;
    }
    
    resultsDiv.innerHTML = results.map((res, i) => {
        const rawHtml = marked.parse(res.content || '');
        const cleanHtml = DOMPurify.sanitize(rawHtml);
        return `
        <div class="b-result">
            <div class="b-result__content b-markdown">${cleanHtml}</div>
            <div class="b-result__refs">
                <div class="b-result__refs-title">Ссылки:</div>
                <ol class="b-result__refs-list">
                    ${
                        res.refs.map((ref) => {
                            return (
                            `<li class="b-result__ref">
                                <div class="b-result__ref-path">[${(ref.id || '')}]. ${ref.filepath}</div>
                                <div class="b-result__ref-note">${(ref.note || '')}</div>
                            </li>`);
                        }).join('')
                    }
                </ol>
            </div>
        </div>
        `;
    }).join('');
}

async function addDocument() {
    const inputFilepath = document.getElementById('file_path');

    const filepathArray = inputFilepath.value.trim().split("\n").filter(s => s.trim())

    if (!filepathArray.length) {
        showStatus('add-status', 'Введите путь к файлу', 'error');
        return;
    }

    for (let filepath of filepathArray) {
        if (!validateFilePath(filepath)) {
            showStatus(
                'add-status', 
                `Неподдерживаемый формат. Разрешены: ${ALLOWED_EXTENSIONS.join(', ')}`, 
                'error'
            );
            return;
        }
    }
    
    hideStatus('add-status');
    setLoading('add-btn', true);

    try {
        const response = await fetch(`${API_BASE}/api/index/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filepath: filepathArray })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showStatus('add-status', data.error, 'error');
        } else {
            showStatus('add-status', data.message || 'Документ успешно добавлен в индекс', 'success');
            inputFilepath.value = '';
        }
    } catch (err) {
        showStatus('add-status', 'Ошибка соединения с сервером', 'error');
    } finally {
        setLoading('add-btn', false);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('search-btn');
    if (searchBtn) {
        searchBtn.dataset.originalText = searchBtn.textContent;
        searchBtn.addEventListener('click', searchDocuments);
        
        document.getElementById('query')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchDocuments();
        });
    }
    
    const addBtn = document.getElementById('add-btn');
    if (addBtn) {
        addBtn.dataset.originalText = addBtn.textContent;
        addBtn.addEventListener('click', addDocument);
        
        document.getElementById('file_path')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') addDocument();
        });
    }
    
    const currentPath = window.location.pathname;
    document.querySelectorAll('.b-nav__link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('b-nav__link_active');
        }
    });

    const pathInput = document.getElementById('file_path');

    if (pathInput) {
        pathInput.placeholder = ""
            + "Построчно:"
            + "\nZ:/Имя Фамилия/file_1.pdf"
            + "\nZ:/Имя Фамилия/file_2.pdf"
            + "\nZ:/Имя Фамилия/file_3.pdf"
    }
});
