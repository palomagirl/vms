# Django
from django.core.exceptions import ObjectDoesNotExist

#local Django
from event.models import Event
from job.models import Job
from job.services import get_jobs_by_event_id, remove_empty_jobs_for_volunteer
from shift.models import Shift
from shift.services import get_volunteer_shifts_with_hours, get_unlogged_shifts_by_volunteer_id


def event_not_empty(event_id):
    """ Checks if the event exists and is not empty """
    result = True
    event = get_event_by_id(event_id)
    if not event:
        result = False
    return result


def get_event_by_shift_id(shift_id):
    """
    Returns an event for the shift. Can be helpful for finding an event
    """
    is_valid = True
    result = None

    try:
        shift = Shift.objects.get(pk=shift_id)
        event = shift.job.event
    except ObjectDoesNotExist:
        is_valid = False

    if is_valid:
        result = event

    return result

def delete_event(event_id):
    """ 
    Deletes an event if no jobs are associated with it
    """

    result = True
    event = get_event_by_id(event_id)

    if event_not_empty(event_id):
        # check if there are currently any jobs associated with this event
        jobs_in_event = event.job_set.all()

        # can only delete an event if no jobs are currently associated with it
        if event and (not jobs_in_event):
            event.delete()
        else:
            result = False
    else:
        result = False

    return result

def check_edit_event(event_id, new_start_date, new_end_date):
    """
    Checks if an event can be edited without resulting in invalid job or shift dates
    """
    result = True
    invalid_count = 0
    invalid_jobs = []
    event = get_event_by_id(event_id)

    if event_not_empty(event_id) and event:

        jobs_in_event = event.job_set.all()
        # check if there are currently any jobs associated with this event
        if jobs_in_event:
            for job in jobs_in_event:
                if( job.start_date < new_start_date or job.end_date > new_end_date):
                    result = False
                    invalid_count += 1
                    invalid_jobs.append(job.name)

    else:
        result = False

    return {'result' : result, 'invalid_count': invalid_count, 'invalid_jobs': invalid_jobs}


def get_event_by_id(event_id):

    is_valid = True
    result = None

    try:
        event = Event.objects.get(pk=event_id)
    except ObjectDoesNotExist:
        is_valid = False

    if is_valid:
        result = event

    return result


def get_events_by_date(start_date, end_date):
    is_valid = True
    result = None
    kwargs = {}
    if start_date:
        kwargs['start_date__gte'] = start_date
    if end_date:
        kwargs['start_date__lte'] = end_date
    try:
        event_list = Event.objects.filter(
                **kwargs
                ).order_by('start_date')
    except ObjectDoesNotExist:
        is_valid = False

    if is_valid:
        result = event_list

    return result

def get_events_ordered_by_name():
    event_list = Event.objects.all().order_by('name')
    return event_list

def get_signed_up_events_for_volunteer(volunteer_id):
    """ Gets sorted list of signed up events for a volunteer """

    event_list = []
    unsorted_events = []
    shift_list_without_hours = get_unlogged_shifts_by_volunteer_id(volunteer_id)
    shift_list_with_hours = get_volunteer_shifts_with_hours(volunteer_id)

    for shift_with_hours in shift_list_with_hours:
        event_name = str(shift_with_hours.shift.job.event.name)
        if event_name not in unsorted_events:
            unsorted_events.append(event_name)
    for shift in shift_list_without_hours:
        event_name = str(shift.job.event.name)
        if event_name not in unsorted_events:
            unsorted_events.append(event_name)

    #for sorting events alphabetically
    for event in sorted(unsorted_events, key=str.lower):
        event_list.append(event)
    return event_list

def remove_empty_events_for_volunteer(event_list, volunteer_id):
    """ Removes all events from an event list without jobs or shifts """
    new_event_list = []
    for event in event_list:
        job_list = get_jobs_by_event_id(event.id)
        job_list = remove_empty_jobs_for_volunteer(job_list, volunteer_id)
        if job_list:
            new_event_list.append(event)
    return new_event_list
