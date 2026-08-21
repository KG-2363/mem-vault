-- Fact table: full photo lifecycle (one row per photo)
with uploads as (
    select * from {{ ref('stg_uploads') }}
),

enhancements as (
    select * from {{ ref('stg_enhancements') }}
),

joined as (
    select
        u.photo_id,
        u.album_id,
        u.tenant_id,
        u.gcs_raw_path,
        u.uploaded_at,
        e.gcs_enhanced_path,
        e.enhanced_at,
        timestamp_diff(e.enhanced_at, u.uploaded_at, second) as enhancement_latency_seconds,
        case
            when e.photo_id is not null then 'ENHANCED'
            else 'UPLOADED'
        end as current_status
    from uploads u
    left join enhancements e using (photo_id, tenant_id)
)

select * from joined
