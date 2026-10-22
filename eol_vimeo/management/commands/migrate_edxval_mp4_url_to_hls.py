"""
Migrate video URLs in edxval linked to a EolVimeo object from the mp4 format (progressive, with or without a domain) to their HLS version (.m3u8).
Usage:
    python manage.py lms --settings=prod.production migrate_edxval_mp4_url_to_hls --dry_run
    python manage.py lms --settings=prod.production migrate_edxval_mp4_url_to_hls
    python manage.py lms --settings=prod.production migrate_edxval_mp4_url_to_hls --sleep_seconds_api 0.5
"""
# Python Standard Libraries
import csv
from datetime import datetime
import logging
import os
import time

# Installed packages (via pip)
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# Edx dependencies
from edxval.models import EncodedVideo

# Internal project dependencies
from eol_vimeo.models import EolVimeoVideo
from eol_vimeo.vimeo_utils import get_video_vimeo, get_link_video

logger = logging.getLogger(__name__)

def get_hls_link(video_data):
    """
        Returns HLS link of the video using get_link_video or None if it doesn't exists.
    """
    video = get_link_video(video_data)
    if video and video.get('link'):
        return video['link']
    return None

class Command(BaseCommand):
    help = 'Migrate mp4 video URLs from edxval linked to a EolVimeo object to their HLS versions by querying the Vimeo API.'

    def add_arguments(self, parser):
        parser.add_argument('--dry_run', action='store_true')
        parser.add_argument('--sleep_seconds_api', type=float, default=0.3, help='Pause between requests to the Vimeo API to avoid reaching the rate limit.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        mode = 'DRY RUN' if dry_run else 'REAL EXECUTION'
        self.stdout.write('=== migrate_edxval_mp4_url_to_hls [{}] ==='.format(mode))

        # Schema length limit for url field in model EncodedVideo
        encoded_max_length = EncodedVideo._meta.get_field('url').max_length
        self.stdout.write('Max length EncodedVideo.url: {}'.format(encoded_max_length))

        # Videos uploaded by eol_vimeo with a valid Vimeo id
        eol_vimeo_videos = {eol_vimeo_video.edx_video_id: eol_vimeo_video for eol_vimeo_video in EolVimeoVideo.objects.exclude(vimeo_video_id='')}
        self.stdout.write('Videos on EolVimeoVideo with vimeo_video_id: {}'.format(len(eol_vimeo_videos)))
        if not eol_vimeo_videos:
            self.stdout.write(self.style.WARNING('There are no videos from EolVimeoVideo to modify.'))
            return

        # The URL is stored in EncodedVideo model, which is filtered through its fk to Video model to match by edx_video_id.
        # Only items that its URL is not in HLS format are going to be modified.
        encoded_videos = list(EncodedVideo.objects.filter(video__edx_video_id__in=list(eol_vimeo_videos.keys()))
                        .exclude(url__contains='.m3u8')
                        .select_related('video')
                        .order_by('id'))
        total = len(encoded_videos)
        self.stdout.write('EncodedVideo with non HLS URLs found: {}'.format(total))

        if total == 0:
            self.stdout.write(self.style.SUCCESS('There are no URLs to migrate. The migration has already been applied or is not necessary.'))
            return

        updated = 0
        unchanged = 0
        errors = 0
        no_response = 0
        no_hls = 0
        too_long = 0
        hls_cache = {}
        completed = False
        csv_path = os.path.join('.', 'migrate_edxval_mp4_url_to_hls_{}_{}.csv'.format(mode, datetime.now().strftime('%Y%m%d_%H%M%S')))
        csv_file = open(csv_path, 'a', newline='', encoding='utf-8')
        writer = csv.DictWriter(csv_file, fieldnames=['encoded_id', 'edx_video_id', 'eol_vimeo_video_id', 'vimeo_id', 'old_url', 'new_url', 'status'])
        writer.writeheader()
        try:
            for index, encoded in enumerate(encoded_videos):
                edx_video_id = encoded.video.edx_video_id
                eol_vimeo_video = eol_vimeo_videos[edx_video_id]
                vimeo_id = eol_vimeo_video.vimeo_video_id

                # If the Vimeo video was already queried, use that. Otherwise, query the Vimeo API.
                if vimeo_id not in hls_cache:
                    try:
                        video_data = get_video_vimeo(vimeo_id)
                        hls_cache[vimeo_id] = get_hls_link(video_data) if video_data else False
                    except Exception:
                        logger.exception('Error querying Vimeo vimeo_id={}'.format(vimeo_id))
                        hls_cache[vimeo_id] = False
                    time.sleep(options['sleep_seconds_api'])
                hls_link = hls_cache[vimeo_id]

                if hls_link is False:
                    no_response += 1
                    status = 'no_response'
                    self.stdout.write(self.style.WARNING('  Video without API Vimeo response: id={} video={} vimeo_id={}'.format(encoded.id, edx_video_id, vimeo_id)))
                elif hls_link is None:
                    no_hls += 1
                    status = 'no_hls'
                    self.stdout.write(self.style.WARNING('  Video without HLS link: id={} video={} vimeo_id={}'.format(encoded.id, edx_video_id, vimeo_id)))
                elif len(hls_link) > encoded_max_length:
                    too_long += 1
                    status = 'too_long'
                    self.stdout.write(self.style.WARNING('  Url longer than encoded_max_length: id={} video={} vimeo_id={} length={}'.format(encoded.id, edx_video_id, vimeo_id, len(hls_link))))
                else:
                    self.stdout.write('  id={} video={}\n    {}\n    -> {}'.format(encoded.id, edx_video_id, encoded.url, hls_link))

                    if dry_run:
                        updated += 1
                        status = 'would_update'
                    else:
                        try:
                            # One short transaction per video: committed immediately
                            with transaction.atomic():
                                # Filter by old URL to avoid overwriting concurrent changes
                                rows = EncodedVideo.objects.filter(id=encoded.id, url=encoded.url).update(url=hls_link)
                                if rows:
                                    EolVimeoVideo.objects.filter(id=eol_vimeo_video.id).update(url_vimeo=hls_link)
                            if rows:
                                updated += 1
                                status = 'updated'
                            else:
                                unchanged += 1
                                status = 'unchanged'
                        except Exception as e:
                            errors += 1
                            status = 'error'
                            logger.exception('Error migrating to HLS EncodedVideo id={}'.format(encoded.id))
                            self.stdout.write(self.style.ERROR('  Error in id={} video={}: {}'.format(encoded.id, edx_video_id, e)))
                writer.writerows([{'encoded_id': encoded.id, 'edx_video_id': edx_video_id, 'eol_vimeo_video_id': eol_vimeo_video.id, 'vimeo_id': vimeo_id, 'old_url': encoded.url, 'new_url': hls_link or '', 'status': status}]) # Writes each row directly with append to the csv file
                self.stdout.write(self.style.WARNING('Row written to csv {}.'.format(csv_path)))
                if (index+1) % 50 == 0:
                    self.stdout.write('  Progress: {}/{} (updated={})'.format((index+1), total, updated))
            completed = True
        finally:
            # Runs on success, on any exception and on Ctrl+C. Always save what was processed so far
            if not completed:
                self.stderr.write(self.style.ERROR('Process interrupted after {}/{} videos.'.format(updated+unchanged, total)))
            if csv_path:
                self.stdout.write('CSV backup written to: {}'.format(csv_path))
            else:
                self.stderr.write(self.style.ERROR('Could not write CSV backup.'))
        csv_file.close()
        skipped = no_response + no_hls + too_long
        self.stdout.write('=== Summary ===')
        self.stdout.write('  {}: {}'.format('Would update' if dry_run else 'Updated', updated))
        self.stdout.write('  No changes (URL changed concurrently): {}'.format(unchanged))
        self.stdout.write('  Omitted: {} (no response={}, no HLS={}, too long={})'.format(skipped, no_response, no_hls, too_long))
        self.stdout.write('  Errors: {}'.format(errors))

        if dry_run:
            self.stdout.write(self.style.SUCCESS('[DRY RUN] No writes performed. The database was not modified.'))
        elif errors or skipped:
            self.stdout.write(self.style.WARNING('Migration completed with comments. Review the specified records. Re-running will retry only pending URLs.'))
        else:
            self.stdout.write(self.style.SUCCESS('Migration completed successfully.'))
