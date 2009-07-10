begin transaction;
insert into languages (lang_code, lang_name, family, iso_code) values
  ("xhit", "Hittite", "Indo-European", "hit");
insert into languages (lang_code, lang_name, family, iso_code) values
  ("xxto", "Tocharian A", "Indo-European", "xto");
insert into languages (lang_code, lang_name, family, iso_code) values
  ("xtxb", "Tocharian B", "Indo-European", "txb");
commit;
