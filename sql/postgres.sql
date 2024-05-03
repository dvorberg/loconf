BEGIN;

CREATE TABLE roster
(
   address INTEGER PRIMARY KEY,
   identifyer TEXT,
   name TEXT
);   

CREATE TABLE revision
(
   id SERIAL PRIMARY KEY,
   address INTEGER NOT NULL, 
   comment TEXT NOT NULL DEFAULT '',
   ctime TIMESTAMP NOT NULL DEFAULT NOW()
);   

CREATE TABLE value
(
   revision_id INTEGER REFERENCES revision,
   cv SMALLINT NOT NULL,
   value SMALLINT NOT NULL,

   UNIQUE (revision_id, cv)
);

COMMIT;
