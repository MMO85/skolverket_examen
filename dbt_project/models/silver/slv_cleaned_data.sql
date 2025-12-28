-- models/silver/slv_cleaned_data.sql
-- Silver layer: normalize raw staged lines into a simple cleaned table.
-- Works even when the raw staging table only contains raw_line + source_file.

with base as (
    select
        source_file,
        raw_line as statistik_text,

        -- Extract first URL-like token if present, otherwise NULL
        nullif(
            regexp_extract(raw_line, '(https?://[^\\s;,"\\)]+)', 1),
            ''
        ) as url_value

    from {{ ref('stg_raw_data') }}
)

select
    statistik_text,
    url_value,
    source_file
from base
where statistik_text is not null
