{{ config(materialized='view') }}

select
  source_file,
  count(*) as n_lines
from {{ source('staging_data','raw_data') }}
group by 1
order by n_lines desc
