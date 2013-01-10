-- MySQL dump 10.13  Distrib 5.1.41, for debian-linux-gnu (i486)
--
-- Host: xambo    Database: dl
-- ------------------------------------------------------
-- Server version	5.1.51-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounttypes`
--

DROP TABLE IF EXISTS `accounttypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounttypes` (
  `accounttypeid` int(11) NOT NULL AUTO_INCREMENT,
  `accountname` text NOT NULL,
  `datefield` int(11) NOT NULL,
  `typefield` int(11) DEFAULT NULL,
  `descriptionfield` int(11) NOT NULL,
  `creditfield` int(11) DEFAULT NULL,
  `debitfield` int(11) DEFAULT NULL,
  `balancefield` int(11) DEFAULT NULL,
  `currencysign` int(11) NOT NULL DEFAULT '1',
  `dateformat` text NOT NULL,
  PRIMARY KEY (`accounttypeid`),
  UNIQUE KEY `accounttypes_unique_name` (`accountname`(64))
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `codes`
--

DROP TABLE IF EXISTS `codes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `codes` (
  `codeid` int(11) NOT NULL AUTO_INCREMENT,
  `code` text NOT NULL,
  `description` text,
  PRIMARY KEY (`codeid`),
  UNIQUE KEY `codes_unique_code` (`code`(128))
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `records`
--

DROP TABLE IF EXISTS `records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `records` (
  `recordid` int(11) NOT NULL AUTO_INCREMENT,
  `checked` tinyint(1) NOT NULL DEFAULT '0',
  `checkdate` datetime DEFAULT NULL,
  `date` date NOT NULL,
  `codeid` int(11) DEFAULT NULL,
  `userid` int(11) NOT NULL,
  `accounttypeid` int(11) NOT NULL,
  `description` text NOT NULL,
  `txdate` datetime DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL,
  `balance` decimal(15,2) DEFAULT NULL,
  `insertdate` datetime DEFAULT NULL,
  `rawdata` text NOT NULL,
  `md5` varchar(32) NOT NULL,
  PRIMARY KEY (`recordid`),
  UNIQUE KEY `records_unique_record` (`userid`,`accounttypeid`,`md5`),
  KEY `records_accounttype_fkey` (`accounttypeid`),
  KEY `records_code_fkey` (`codeid`),
  KEY `records_user_fkey` (`userid`),
  CONSTRAINT `records_user_fkey` FOREIGN KEY (`userid`) REFERENCES `users` (`userid`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `records_accounttype_fkey` FOREIGN KEY (`accounttypeid`) REFERENCES `accounttypes` (`accounttypeid`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `records_code_fkey` FOREIGN KEY (`codeid`) REFERENCES `codes` (`codeid`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=2415 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recordtags`
--

DROP TABLE IF EXISTS `recordtags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `recordtags` (
  `recordtagid` int(11) NOT NULL AUTO_INCREMENT,
  `recordid` int(11) NOT NULL,
  `tagid` int(11) NOT NULL,
  PRIMARY KEY (`recordtagid`),
  UNIQUE KEY `recordtags_unique_tag` (`recordid`,`tagid`),
  KEY `recordtags_record_fkey` (`recordid`),
  KEY `recordtags_tag_fkey` (`tagid`),
  CONSTRAINT `recordtags_tag_fkey` FOREIGN KEY (`tagid`) REFERENCES `tags` (`tagid`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `recordtags_record_fkey` FOREIGN KEY (`recordid`) REFERENCES `records` (`recordid`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tags`
--

DROP TABLE IF EXISTS `tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tags` (
  `tagid` int(11) NOT NULL AUTO_INCREMENT,
  `tagname` text NOT NULL,
  `userid` int(11) NOT NULL,
  PRIMARY KEY (`tagid`),
  UNIQUE KEY `tags_unique_record` (`tagname`(128),`userid`) USING BTREE,
  KEY `tags_user_fkey` (`userid`),
  CONSTRAINT `tags_user_fkey` FOREIGN KEY (`userid`) REFERENCES `users` (`userid`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `userid` int(11) NOT NULL AUTO_INCREMENT,
  `username` text NOT NULL,
  PRIMARY KEY (`userid`),
  UNIQUE KEY `users_unique_name` (`username`(128))
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2010-10-24  0:34:49
