-- جدول المستخدمين
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10),
    is_premium BOOLEAN DEFAULT FALSE,
    premium_expires TIMESTAMP,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    daily_usage INTEGER DEFAULT 0,
    total_operations INTEGER DEFAULT 0
);

-- جدول سجل العمليات
CREATE TABLE operations_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    operation VARCHAR(50) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time INTERVAL,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    file_size BIGINT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- جدول الملفات المؤقتة
CREATE TABLE temp_files (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    file_id VARCHAR(200) NOT NULL,
    file_name VARCHAR(255),
    file_size BIGINT,
    file_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '1 day'),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- جدول إعدادات البوت
CREATE TABLE bot_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول الإحصائيات اليومية
CREATE TABLE daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    premium_users INTEGER DEFAULT 0,
    total_operations INTEGER DEFAULT 0,
    operations_by_type JSONB,
    revenue DECIMAL(10, 2) DEFAULT 0,
    UNIQUE(date)
);

-- فهارس للأداء
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_operations_user_id ON operations_log(user_id);
CREATE INDEX idx_operations_timestamp ON operations_log(timestamp);
CREATE INDEX idx_temp_files_expires ON temp_files(expires_at);

-- دالة تنظيف الملفات المؤقتة
CREATE OR REPLACE FUNCTION cleanup_expired_files()
RETURNS void AS $$
BEGIN
    DELETE FROM temp_files 
    WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- جدولة المهمة لتنظيف الملفات كل ساعة
SELECT cron.schedule('cleanup-temp-files', '0 * * * *', 'SELECT cleanup_expired_files();');

-- إدراج الإعدادات الافتراضية
INSERT INTO bot_settings (setting_key, setting_value, description) VALUES
('max_file_size', '52428800', 'الحد الأقصى لحجم الملف بالبايت (50MB)'),
('free_daily_limit', '5', 'الحد اليومي للمستخدمين المجانيين'),
('premium_daily_limit', '100', 'الحد اليومي للمستخدمين المدفوعين'),
('premium_monthly_price', '9.99', 'سعر الاشتراك الشهري'),
('premium_yearly_price', '99.99', 'سعر الاشتراك السنوي'),
('maintenance_mode', 'false', 'وضع الصيانة'),
('welcome_message', 'مرحباً بك في أقوى بوت PDF!', 'رسالة الترحيب');

-- إنشاء مستخدم إداري افتراضي
INSERT INTO users (user_id, username, first_name, is_premium) 
VALUES (123456789, 'admin', 'Administrator', true)
ON CONFLICT (user_id) DO NOTHING;
