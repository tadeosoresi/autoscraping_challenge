CREATE TABLE `buses_images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(64) DEFAULT NULL,
  `url` varchar(1000) DEFAULT NULL,
  `description` longtext DEFAULT NULL,
  `image_index` int DEFAULT 0,
  `bus_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `busId` (`bus_id`) USING BTREE,
  CONSTRAINT `buses_images_ibfk_1` FOREIGN KEY (`bus_id`) REFERENCES `buses` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
