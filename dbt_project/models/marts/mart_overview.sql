select
    statistik_text,
    url_value,
    source_file
from {{ ref('slv_cleaned_data') }}
