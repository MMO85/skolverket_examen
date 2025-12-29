select
  raw_line,
  source_file
from {{ source('staging_data', 'raw_data') }}
