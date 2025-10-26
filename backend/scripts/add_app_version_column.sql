-- 新增 app_version 欄位到 activations 表格
ALTER TABLE activations ADD COLUMN app_version VARCHAR(50);
