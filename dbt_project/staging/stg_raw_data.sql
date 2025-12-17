{{ config(materialized='table') }}

select
    statistik_fr_n_skolverket as raw_line,
    https_www_skolverket_se   as skolverket_url,
    source_file
from {{ source('skolverket', 'raw_data') }}
