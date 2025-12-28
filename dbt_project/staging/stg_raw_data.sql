{{ config(materialized='table') }}

select
  raw_line,
  source_file
from {{ source('skolverket', 'raw_data') }}
