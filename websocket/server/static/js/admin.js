// RAG Admin Interface JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeInterface();
});

// Global variables
let documents = [];
let filteredDocuments = [];

// Initialize the interface
function initializeInterface() {
    loadDocuments();
    setupEventListeners();
    updateStats();
}

// Setup event listeners
function setupEventListeners() {
    // Upload type change
    const uploadTypeRadios = document.getElementsByName('uploadType');
    uploadTypeRadios.forEach(radio => {
        radio.addEventListener('change', toggleUploadType);
    });
    
    // Form submission
    document.getElementById('uploadForm').addEventListener('submit', handleUpload);
    
    // Search functionality
    document.getElementById('searchDocs').addEventListener('input', filterDocuments);
    
    // Tab changes
    document.getElementById('stats-tab').addEventListener('click', loadCharts);
}

// Toggle between text and file upload
function toggleUploadType() {
    const uploadType = document.querySelector('input[name="uploadType"]:checked').value;
    const textArea = document.getElementById('text-upload-area');
    const fileArea = document.getElementById('file-upload-area');
    
    if (uploadType === 'text') {
        textArea.style.display = 'block';
        fileArea.style.display = 'none';
        document.getElementById('content').required = true;
        document.getElementById('fileInput').required = false;
    } else {
        textArea.style.display = 'none';
        fileArea.style.display = 'block';
        document.getElementById('content').required = false;
        document.getElementById('fileInput').required = true;
    }
}

// Handle form submission
async function handleUpload(event) {
    event.preventDefault();
    
    // Validate form
    if (!validateForm()) {
        return;
    }
    
    const formData = getFormData();
    
    try {
        showLoading(true);
        
        const response = await fetch('/admin/upload-document', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('تم تحميل الوثيقة بنجاح!', 'success');
            document.getElementById('uploadForm').reset();
            toggleUploadType();
            loadDocuments();
            updateStats();
        } else {
            showAlert('فشل في تحميل الوثيقة: ' + result.error, 'error');
        }
    } catch (error) {
        showAlert('حدث خطأ في التحميل: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Validate form inputs
function validateForm() {
    clearErrors();
    let isValid = true;
    
    const requiredFields = ['title', 'department', 'category', 'language'];
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field.value.trim()) {
            showFieldError(fieldId, 'هذا الحقل مطلوب');
            isValid = false;
        }
    });
    
    const uploadType = document.querySelector('input[name="uploadType"]:checked').value;
    if (uploadType === 'text') {
        const content = document.getElementById('content');
        if (!content.value.trim()) {
            showFieldError('content', 'محتوى الوثيقة مطلوب');
            isValid = false;
        }
    } else {
        const fileInput = document.getElementById('fileInput');
        if (!fileInput.files || fileInput.files.length === 0) {
            showFieldError('file', 'ملف الوثيقة مطلوب');
            isValid = false;
        }
    }
    
    return isValid;
}

// Get form data
function getFormData() {
    const formData = {
        title: document.getElementById('title').value.trim(),
        department: document.getElementById('department').value,
        category: document.getElementById('category').value,
        language: document.getElementById('language').value,
        author: document.getElementById('author').value.trim() || 'غير محدد',
        version: document.getElementById('version').value.trim() || '1.0',
        tags: document.getElementById('tags').value.trim().split(',').map(tag => tag.trim()).filter(tag => tag),
        uploadType: document.querySelector('input[name="uploadType"]:checked').value
    };
    
    const uploadType = formData.uploadType;
    if (uploadType === 'text') {
        formData.content = document.getElementById('content').value.trim();
    } else {
        // For file upload, file will be sent separately
        const fileInput = document.getElementById('fileInput');
        if (fileInput.files && fileInput.files.length > 0) {
            formData.fileName = fileInput.files[0].name;
            formData.fileSize = fileInput.files[0].size;
        }
    }
    
    return formData;
}

// Show field error
function showFieldError(fieldId, message) {
    const errorElement = document.getElementById(fieldId + '-error');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

// Clear all errors
function clearErrors() {
    const errorElements = document.getElementsByClassName('error-message');
    Array.from(errorElements).forEach(element => {
        element.style.display = 'none';
        element.textContent = '';
    });
}

// Show alert
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.getElementsByClassName('alert-temporary');
    Array.from(existingAlerts).forEach(alert => alert.remove());
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-temporary`;
    alertDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
        ${message}
    `;
    
    // Insert at top of main container
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Show loading state
function showLoading(isLoading) {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (isLoading) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري التحميل...';
        submitBtn.disabled = true;
    } else {
        submitBtn.innerHTML = '<i class="fas fa-upload me-2"></i>تحميل الوثيقة';
        submitBtn.disabled = false;
    }
}

// Load documents
async function loadDocuments() {
    try {
        const response = await fetch('/admin/documents');
        const result = await response.json();
        
        if (result.success) {
            documents = result.documents;
            filteredDocuments = documents;
            displayDocuments();
            updateStats();
        } else {
            showAlert('فشل في تحميل الوثائق: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        document.getElementById('documents-list').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                حدث خطأ في تحميل الوثائق. تأكد من تشغيل الخادم.
            </div>
        `;
    }
}

// Display documents
function displayDocuments() {
    const container = document.getElementById('documents-list');
    
    if (filteredDocuments.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-folder-open fa-2x mb-2"></i>
                <p>لا توجد وثائق تطابق المعايير المحددة</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    filteredDocuments.forEach((doc, index) => {
        const docElement = createDocumentElement(doc, index);
        container.appendChild(docElement);
    });
}

// Create document element
function createDocumentElement(doc, index) {
    const div = document.createElement('div');
    div.className = 'document-item';
    div.innerHTML = `
        <div class="form-check form-check-inline">
            <input class="form-check-input" type="checkbox" value="${doc.document_id}" id="doc-${index}">
        </div>
        <div class="d-flex justify-content-between align-items-start">
            <div class="flex-grow-1">
                <h6 class="mb-1">${doc.title}</h6>
                <p class="text-muted mb-2">${doc.author || 'غير محدد'}</p>
                <div class="badges mb-2">
                    <span class="badge bg-primary me-1">${doc.department.trim()}</span>
                    <span class="badge bg-secondary me-1">${doc.category}</span>
                    <span class="badge bg-info me-1">${doc.language}</span>
                    <span class="badge bg-warning me-1">${doc.version}</span>
                </div>
                <small class="text-muted">تاريخ النشر: ${new Date(doc.created_date).toLocaleDateString('ar-SA')}</small>
            </div>
            <div class="doc-actions">
                <button class="btn btn-sm btn-outline-primary me-1" onclick="viewDocument('${doc.document_id}')">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteDocument('${doc.document_id}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    return div;
}

// Filter documents
function filterDocuments() {
    const searchTerm = document.getElementById('searchDocs').value.toLowerCase();
    const departmentFilter = document.getElementById('filterDepartment').value;
    const categoryFilter = document.getElementById('filterCategory').value;
    
    filteredDocuments = documents.filter(doc => {
        const matchesSearch = doc.title.toLowerCase().includes(doc) ||
                             doc.author.toLowerCase().includes(searchTerm);
        const matchesDepartment = !departmentFilter || doc.department === departmentFilter;
        const matchesCategory = !categoryFilter || doc.category === categoryFilter;
        
        return matchesSearch && matchesDepartment && matchesCategory;
    });
    
    displayDocuments();
}

// Load template
function loadTemplate(templateType) {
    const templates = {
        hr: {
            title: 'سياسة موارد بشرية جديدة',
            department: 'HR',
            category: 'policies',
            author: 'إدارة الموارد البشرية',
            content: `
# عنوان السياسة

## القسم الأول
كيف هذا القسم من السياسة...

## القسم الثاني  
كيف هذا الجزء الثاني...

## القسم الثالث
كيف هنا الحلقة الثالثة...
            `
        },
        it: {
            title: 'سياسة تقنية معلومات جديدة',
            department: 'IT',
            category: 'procedures',
            author: 'قسم تقنية المعلومات',
            content: `
# سياسة تقنية المعلومات

## المتطلبات الأمنية
- استخدام كلمات مرور قوية
- تحديث الأنظمة بانتظام
- النسخ الاحتياطي للبيانات

## سياسات الاستخدام
- استخدام الأجهزة المقسمة للعمل فقط
- عدم تنزيل البرامج غير المرخصة
- الالتزام بساعات العمل المحددة
            `
        },
        announcement: {
            title: 'إعلان رسمي',
            department: 'Admin',
            category: 'announcements',
            author: 'الإدارة العامة',
            content: `
# إعلان مهم

تاريخ النشر: ${new Date().toLocaleDateString('ar-SA')}

## الموضوع
نكتب هنا موضوع الإعلان...

## التفاصيل
تُُفاصيل الإعلان المهمة...

## الجهة المسؤولة
من يمكن الاتصال للحصول على مزيد من المعلومات.
            `
        }
    };
    
    if (templates[templateType]) {
        const template = templates[templateType];
        document.getElementById('title').value = template.title;
        document.getElementById('department').value = template.department;
        document.getElementById('category').value = template.category;
        document.getElementById('author').value = template.author;
        document.getElementById('content').value = template.content;
        document.getElementById('uploadText').checked = true;
        toggleUploadType();
    }
}

// View document
async function viewDocument(documentId) {
    try {
        const response = await fetch(`/admin/document/${documentId}`);
        const result = await response.json();
        
        if (result.success) {
            alert(`العنوان: ${result.document.title}\n\nالمحتوى:\n${result.document.content}`);
        } else {
            showAlert('فشل في عرض الوثيقة: ' + result.error, 'error');
        }
    } catch (error) {
        showAlert('حدث خطأ: ' + error.message, 'error');
    }
}

// Delete document
async function deleteDocument(documentId) {
    if (confirm('هل أنت متأكد من حذف هذه الوثيقة؟ لا يمكن التراجع عن هذا الإجراء.')) {
        try {
            const response = await fetch(`/admin/document/${documentId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                showAlert('تم حذف الوثيقة بنجاح', 'success');
                loadDocuments();
                updateStats();
            } else {
                showAlert('فشل في حذف الوثيقة: ' + result.error, 'error');
            }
        } catch (error) {
            showAlert('حدث خطأ: ' + error.message, 'error');
        }
    }
}

// Delete selected documents
async function deleteSelected() {
    const checkboxes = document.getElementsByClassName('form-check-input');
    const selectedDocs = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);
    
    if (selectedDocs.length === 0) {
        showAlert('يرجى تحديد وثائق للحذف', 'error');
        return;
    }
    
    if (confirm(`هل أنت متأكد من حذف ${selectedDocs.length} وثيقة؟`)) {
        try {
            const response = await fetch('/admin/documents', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ documents: selectedDocs })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showAlert(`تم حذف ${selectedDocs.length} وثيقة بنجاح`, 'success');
                loadDocuments();
                updateStats();
            } else {
                showAlert('فشل في حذف الوثائق: ' + result.error, 'error');
            }
        } catch (error) {
            showAlert('فعل خطأ: ' + error.message, 'error');
        }
    }
}

// Refresh documents
function refreshDocuments() {
    loadDocuments();
}

// Test query
async function testQuerySystem() {
    const query = document.getElementById('testQuery').value.trim();
    const language = document.getElementById('testLanguage').value;
    
    if (!query) {
        showAlert('يرجى كتابة استعلام للاختبار', 'error');
        return;
    }
    
    try {
        const response = await fetch('/admin/test-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, language })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayTestResults(result);
        } else {
            showAlert('فشل في تشغيل الاستعلام: ' + result.error, 'error');
        }
    } catch (error) {
        showAlert('حدث خطأ: ' + error.message, 'error');
    }
}

// Display test results
function displayTestResults(result) {
    const resultsDiv = document.getElementById('test-results');
    const answerDiv = document.getElementById('test-answer');
    const sourcesDiv = document.getElementById('test-sources');
    const confidenceDiv = document.getElementById('test-confidence');
    
    answerDiv.textContent = result.answer;
    
    if (result.sources && result.sources.length > 0) {
        sourcesDiv.innerHTML = `
            <h6><i class="fas fa-book me-2"></i>المصادر الرئيسية (${result.sources.length}):</h6>
            <ul class="list-unstyled">
                ${result.sources.map(source => `
                    <li><i class="fas fa-file-alt text-info me-1"></i>${source.title}</li>
                `).join('')}
            </ul>
        `;
    } else {
        sourcesDiv.innerHTML = '<p class="text-muted">لا توجد مصادر متطابقة</p>';
    }
    
    if (result.confidence) {
        confidenceDiv.innerHTML = `
            <div class="progress">
                <div class="progress-bar" role="progressbar" style="width: ${result.confidence * 100}%">
                    ثقة في الإجابة: ${Math.round(result.confidence * 100)}%
                </div>
            </div>
        `;
    }
    
    resultsDiv.style.display = 'block';
}

// Set test query from examples
function setTestQuery(query) {
    document.getElementById('testQuery').value = query;
}

// Update statistics
function updateStats() {
    // Total documents
    document.getElementById('total-docs').textContent = documents.length;
    
    // Unique departments
    const departments = [...new Set(documents.map(doc => doc.department))];
    document.getElementById('total-departments').textContent = departments.length;
    
    // Unique categories
    const categories = [...new Set(documents.map(doc => doc.category))];
    document.getElementById('total-categories').textContent = categories.length;
    
    // Unique languages
    const languages = [...new Set(documents.map(doc => doc.language))];
    document.getElementById('total-languages').textContent = languages.length;
}

// Load charts for statistics
function loadCharts() {
    // Department chart
    const departmentCtx = document.getElementById('departmentChart').getContext('2d');
    const departmentFreq = {};
    documents.forEach(doc => {
        departmentFreq[doc.department] = (departmentFreq[doc.department] || 0) + 1;
    });
    
    new Chart.js(departmentCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(departmentFreq),
            datasets: [{
                data: Object.values(departmentFreq),
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'الوثائق حسب القسم'
                }
            }
        }
    });
    
    // Category chart
    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    const categoryFreq = {};
    documents.forEach(doc => {
        categoryFreq[doc.category] = (categoryFreq[doc.category] || 0) + 1;
    });
    
    new Chart.js(categoryCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(categoryFreq),
            datasets: [{
                label: 'عدد الوثائق',
                data: Object.values(categoryFreq),
                backgroundColor: '#36A2EB'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'الوثائق حسب الفئة'
                }
            }
        }
    });
}

// File input handling
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.querySelector('.upload-area');
    
    if (fileInput && uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.style.backgroundColor = '#f0f8ff';
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadArea.style.backgroundColor = '';
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.style.backgroundColor = '';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                uploadArea.innerHTML = `
                    <i class="fas fa-check fa-3x text-success mb-3"></i>
                    <p class="mb-2">تم اختيار الملف: ${files[0].name}</p>
                    <p class="text-muted small">انقر لاختيار ملف آخر</p>
                `;
            }
        });
        
        fileInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files.length > 0) {
                uploadArea.innerHTML = `
                    <i class="fas fa-check fa-3x text-success mb-3"></i>
                    <p class="mb-2">تم اختيار الملف: ${e.target.files[0].name}</p>
                    <p class="text-muted small">انقر لاختيار ملف آخر</p>
                `;
            }
        });
    }
});
