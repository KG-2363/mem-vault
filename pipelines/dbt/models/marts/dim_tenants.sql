-- Tenant dimension built from upload activity
with tenant_stats as (
    select
        tenant_id,
        count(distinct album_id) as album_count,
        count(photo_id)          as total_photos,
        count(case when current_status = 'ENHANCED' then 1 end) as enhanced_photos,
        min(uploaded_at)         as first_upload_at,
        max(uploaded_at)         as last_upload_at
    from {{ ref('fct_photo_events') }}
    group by tenant_id
)

select
    tenant_id,
    album_count,
    total_photos,
    enhanced_photos,
    round(safe_divide(enhanced_photos, total_photos) * 100, 2) as enhancement_rate_pct,
    first_upload_at,
    last_upload_at,
    current_timestamp() as dbt_updated_at
from tenant_stats
