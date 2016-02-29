-- Inspired by: https://hashrocket.com/blog/posts/faster-json-generation-with-postgresql
-- See also: http://www.postgresql.org/docs/9.3/static/functions-json.html

-- lexicon_lexeme as json entries:
CREATE OR REPLACE VIEW view_json_lexeme AS
SELECT row_to_json(t)
FROM (
    SELECT * FROM lexicon_lexeme
) t;

-- lexicon_meaning as json entries:
SELECT row_to_json(t)
FROM (
    SELECT M.*, array_to_json(array_agg(L.row_to_json))
    FROM lexicon_meaning as M
    JOIN view_json_lexeme AS L
    ON L.row_to_json->>'id' = M.id;
) t;
