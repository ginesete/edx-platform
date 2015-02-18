"""
Certificates API views
"""

import logging
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from courseware import grades
from xmodule.modulestore.django import modulestore
from util.json_request import JsonResponse, JsonResponseBadRequest
from models import CertificateStatuses as cert_status, certificate_status_for_student
from queue import XQueueCertInterface
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError

log = logging.getLogger("edx.certificate")


@require_POST
def generate_user_cert(request, course_id):
    """
    It will add the add-cert request into the xqueue.

     Arguments:
        request (django request object):  the HTTP request object that triggered this view function
        course_id (unicode):  id associated with the course

    Returns:
        returns json response
    """

    if not request.user.is_authenticated():
        log.info(u"Anon user trying to generate certificate for %s", course_id)
        return JsonResponseBadRequest(_('You must be logged-in to generate certificate'))

    student = request.user

    # checking course id
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return JsonResponseBadRequest(_("Course Id is not valid"))

    course = modulestore().get_course(course_key, depth=2)
    if not course:
        return JsonResponseBadRequest(_("Course is not valid"))

    if not is_course_passed(course, None, student, request):
        return JsonResponseBadRequest(_("You failed to pass the course."))

    xqueue = XQueueCertInterface()

    certificate_status = certificate_downloadable_status(student, course_key)
    if not certificate_status["is_downloadable"] and not certificate_status["is_generating"]:
        ret = xqueue.add_cert(student, course_key, course=course)
        log.info(
            (
                u"Added a certificate generation task to the XQueue "
                u"for student %s in course '%s'. "
                u"The new certificate status is '%s'."
            ),
            student.id,
            unicode(course_key),
            ret
        )
        return JsonResponse(_("Certificate generated."))
        # for any other status return bad request response
    return JsonResponseBadRequest('')


def is_course_passed(course, grade_summary=None, student=None, request=None):
    """
    check user's course passing status. return True if passed
    """
    nonzero_cutoffs = [cutoff for cutoff in course.grade_cutoffs.values() if cutoff > 0]
    success_cutoff = min(nonzero_cutoffs) if nonzero_cutoffs else None

    if grade_summary is None:
        grade_summary = grades.grade(student, request, course)

    return success_cutoff and grade_summary['percent'] > success_cutoff


def certificate_downloadable_status(student, course_key):
    """
    check the student existing certificates against a given course.
    if status is not generating and not downloadable or error then user can view the generate button.

    Args:
        student : user object
        course_key :  id associated with the course
    Returns:
        Dict containing student passed status also download url for cert if available
    """
    current_status = certificate_status_for_student(student, course_key)

    response_data = {
        'is_downloadable': False,
        'is_generating': True if current_status['status'] in [cert_status.generating, cert_status.error] else False,
        'download_url': None
    }

    if current_status['status'] == cert_status.downloadable:
        response_data['is_downloadable'] = True
        response_data['download_url'] = current_status['download_url']

    return response_data
