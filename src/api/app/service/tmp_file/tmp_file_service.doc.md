# tmp file service

This module provides services for managing temporary files

## Features

- create tmp file with path and expiration time, default expiration time is 1 hour, if expiration time is before now, the file will be deleted immediately
- tmp file should be recorded in database table tmp_file, scheduler will delete expired tmp files periodically