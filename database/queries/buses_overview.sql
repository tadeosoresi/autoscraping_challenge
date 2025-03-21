CREATE TABLE `buses_overview` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bus_id` int DEFAULT NULL,
  `mdesc` longtext DEFAULT NULL,
  `intdesc` longtext DEFAULT NULL,
  `extdesc` longtext DEFAULT NULL,
  `features` longtext DEFAULT NULL,
  `specs` longtext DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `busId` (`bus_id`),
  CONSTRAINT `buses_overview_ibfk_1` FOREIGN KEY (`bus_id`) REFERENCES `buses` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
