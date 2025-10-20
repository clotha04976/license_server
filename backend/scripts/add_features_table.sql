USE `license_db`;

-- -----------------------------------------------------
-- Table `features`
-- 儲存所有可被授權的功能
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `features` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `description` TEXT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC)
)
ENGINE = InnoDB
COMMENT = '可授權的功能列表';

-- You can insert your initial features like this:
-- INSERT INTO `features` (`name`, `description`) VALUES ('invoice_recognition', 'OCR 辨識功能');
-- INSERT INTO `features` (`name`, `description`) VALUES ('auto_download_invoices', '電子發票自動下載');