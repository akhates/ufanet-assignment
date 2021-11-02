CREATE SCHEMA `tx1tldd7vwazq7z9` ;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY
   'B9xyEXMpfRnqqrN9';
    FLUSH PRIVILEGES;
CREATE TABLE `messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `chat_id` bigint NOT NULL,
  `text` varchar(255) DEFAULT NULL,
  `datetime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `chat_id` bigint DEFAULT NULL,
  `date_joined` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
CREATE TABLE `tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
INSERT INTO `tags` VALUES
(1,'#Python','высокоуровневый язык программирования, ориентированный на повышение производительности разработчика и читаемости кода'),
(2,'#Уфанет','крупный российский интернет-провайдер и оператор кабельного ТВ'),
(3,'#Россия1','второй по значимости национальный телеканал, охватывающий практически всю территорию России'),
(4,'#СТС','«СТС» («Сеть телевизионных станций», наименование СМИ — «Первый развлекательный СТС») — российский федеральный телеканал. Принадлежит холдингу «СТС Медиа».');
