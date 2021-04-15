with
latest_serials as (
	select 
		s.serial_id,
		s.serial_number serial_name,
		s.start serial_start,
		s.end serial_end
	from
		pepys."Serials" s
	where 
		s.end::date::timestamp = (clock_timestamp()::date)-interval '1 day'
),
participating_platforms as (
	select
		ep.platform_id,
		p.name platform_name,
		pt.default_data_interval_secs gap_seconds,
		pt.name platform_type_name,
		ls.serial_start,
		ls.serial_end,
		coalesce(sp.start, ls.serial_start) serial_participant_start,
		coalesce(sp.end, ls.serial_end) serial_participant_end,
		sp.serial_id
	from
		pepys."SerialParticipants" sp
			inner join
		pepys."WargameParticipants" ep
				on sp.wargame_participant_id = ep.wargame_participant_id
			inner join
		pepys."Platforms" p
				on p.platform_id = ep.platform_id
			inner join
		pepys."PlatformTypes" pt
				on p.platform_type_id = pt.platform_type_id
			inner join
		latest_serials ls
				on ls.serial_id = sp.serial_id
)
select
	'SERIALS' record_type,
	s.serial_id,
	NULL platform_id,
	s.serial_name "name",
	NULL platform_type_name,
	s.serial_start "start",
	s.serial_end "end",
	NULL gap_seconds
from
	latest_serials s
union all
select
	'SERIAL PARTICIPANT' record_type,
	pp.serial_id,
	pp.platform_id,
	pp.platform_name "name",
	pp.platform_type_name,
	pp.serial_participant_start "start",
	pp.serial_participant_end "end",
	pp.gap_seconds
from
	participating_platforms pp
union all
select
	distinct
	'PARTICIPANTS' record_type,
	NULL::uuid serial_id,
	pp.platform_id,
	pp.platform_name "name",
	pp.platform_type_name,
	NULL::timestamp "start",
	NULL::timestamp "end",
	NULL::int gap_seconds
from 
	participating_platforms pp
order by 
	record_type desc,
	"name",
	"start",
	"end";
