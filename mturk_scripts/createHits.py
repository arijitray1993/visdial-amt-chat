from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from boto.mturk.qualification import *
from boto.mturk.connection import MTurkRequestError
from constants import *

def create_new_hit_type(is_prod = False):
    if is_prod:
        quals = Qualifications()
        quals.add(NumberHitsApprovedRequirement('GreaterThanOrEqualTo',
                                                        5000,
                                                        required_to_preview=False))
        quals.add(PercentAssignmentsApprovedRequirement('GreaterThanOrEqualTo',
                                                        95,
                                                        required_to_preview=False))
        quals.add(LocaleRequirement('EqualTo',
                                    'US',
                                    required_to_preview=False))
    else:
        quals = None
    new_hit_type = mtc.register_hit_type(title=title,
                                              reward=Price(amount=amountToPay),
                                              description=description,
                                              keywords = keywords,
                                              duration = 1200,
                                              qual_req=quals)
    print new_hit_type[0].HITTypeId
    return new_hit_type[0].HITTypeId

def create_hits(hit_type_id, no_of_hits = NUM_HITS, no_of_assignments = 1, amount = amountToPay, duration = 1200):
    questionform = ExternalQuestion(url, frame_height)
    for _ in xrange(no_of_hits):
        print _
        create_hit_result = mtc.create_hit(
            hit_type = hit_type_id,
            max_assignments = no_of_assignments,
            question = questionform,
            reward = Price(amount=amount),
        )

def cancel_hits():
    count = 0
    count_exp = 0
    pages = 1000 # 100 per page

    for i in range(pages):
        page = i + 1
        hits = mtc.search_hits(sort_direction="Descending", page_size=100, page_number=page)
        for j in hits:
            if j.Title == title:
                try:
                    #print j.HITId
                    mtc.expire_hit(j.HITId)
                    mtc.dispose_hit(j.HITId)
                except MTurkRequestError:
                    print  j.HITId
                    #  assns = mtc.get_assignments(j.HITId)
                    #  for i in assns:
                        #  print 'Approving', j.HITId, i.AssignmentId
                        #  mtc.approve_assignment(i.AssignmentId)
                count += 1
            if count == NUM_HITS:
                break

    print count

def get_results():
    result_hit = []
    all_hits = mtc.get_all_hits()
    for it in all_hits:
        id = it.HITId
        result_hit.append(mtc.get_assignments(id))

    return result_hit

mtc = getConnection(is_prod)
create_hits(create_new_hit_type(is_prod))
# cancel_hits()
