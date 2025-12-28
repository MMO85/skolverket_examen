select
    statistik_fr_n_skolverket       as statistik_text,
    https_www_skolverket_se         as url_value,
    source_file
from {{ ref('stg_raw_data') }}
