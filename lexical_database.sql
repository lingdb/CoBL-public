BEGIN TRANSACTION;

CREATE TABLE languages (
  id INTEGER PRIMARY KEY,
  iso_code TEXT,          -- iso-639-3 ("ethnologue") language code
  ascii_name TEXT,
  utf8_name TEXT,
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE meanings (
  id INTEGER PRIMARY KEY,
  dyen_code INTEGER,      -- Dyen's gloss
  gloss TEXT,             -- short form
  description TEXT,       -- gloss with explanation
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sources (
  id INTEGER PRIMARY KEY,
  type TEXT,              -- "publication", "person"
  description TEXT,
  citation TEXT,
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  CHECK (type in ("publication", "person"))
);

CREATE TABLE dyen_names (
  id INTEGER PRIMARY KEY,
  language_id INTEGER UNIQUE, 
  name TEXT UNIQUE,
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (language_id) REFERENCES languages (id) ON DELETE CASCADE
);

CREATE TABLE abvd_names (
  id INTEGER PRIMARY KEY,
  language_id INTEGER UNIQUE, 
  name TEXT UNIQUE,
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (language_id) REFERENCES languages (id) ON DELETE CASCADE
);

CREATE TABLE lexemes (
  id INTEGER PRIMARY KEY,
  language_id INTEGER UNIQUE, 
  meaning_id INTEGER UNIQUE,
  source_form TEXT,
  phon_form TEXT,
  notes TEXT,
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (language_id) REFERENCES languages (id) ON DELETE CASCADE
  FOREIGN KEY (meaning_id) REFERENCES meanings (id) ON DELETE CASCADE
);

CREATE TABLE cognate_sets (
  id INTEGER PRIMARY KEY,
  reconstruction TEXT,
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cognate_judgements (
  id INTEGER PRIMARY KEY,
  lexeme_id INTEGER, 
  cognate_set_id INTEGER,
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (lexeme_id) REFERENCES lexemes (id) ON DELETE CASCADE
  FOREIGN KEY (cognate_set_id) REFERENCES cognate_sets (id) ON DELETE CASCADE
);

CREATE TABLE cognate_judgement_sources (
  id INTEGER PRIMARY KEY,
  cognate_judgement_id INTEGER,
  source_id INTEGER, 
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (source_id) REFERENCES sources (id) ON DELETE CASCADE
  FOREIGN KEY (cognate_judgement_id) REFERENCES cognate_judgements (id) ON DELETE CASCADE
);

CREATE TABLE lexeme_sources (
  id INTEGER PRIMARY KEY,
  lexeme_id INTEGER,
  source_id INTEGER, 
  datestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (source_id) REFERENCES sources (id) ON DELETE CASCADE
  FOREIGN KEY (lexeme_id) REFERENCES lexemes (id) ON DELETE CASCADE
);

.genfkey --exec

insert into languages (ascii_name) values ("English");
insert into dyen_names (language_id, name) values (1, "ENGLISH");
insert into meanings (dyen_code, gloss) values (4, "ashes");
insert into lexemes (language_id, meaning_id, phon_form) values (1,1,"æ#əz");
insert into cognate_sets (reconstruction) values (NULL);
insert into sources (type, description) values ("book", "OED");
insert into sources (type, description) values ("person", "Dr Johnson");
insert into lexeme_sources (lexeme_id, source_id) values (1, 2);
insert into cognate_judgements (lexeme_id, cognate_set_id) values (1, 1);
insert into cognate_judgement_sources (cognate_judgement_id, source_id) values (1, 1);
COMMIT;
