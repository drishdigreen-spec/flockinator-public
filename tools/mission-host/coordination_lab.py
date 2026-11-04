"""Controlled message interventions for the Flockinator exhibition."""
import random
from collections import Counter
from planner import HOME, random_scenario, simulate
from exercise_memory import label

TRAIN_ROUNDS, TEST_ROUNDS = 48, 32
SECTORS = ('Reed', 'Fern', 'Moss')
LINKS = ('Muted', 'Half lost', 'Scrambled')


def mission_comparison(plan):
    results = []
    traces = []
    for muted in (False, True):
        events = []
        sim = simulate(plan, plan['battery']+2, events, mute_checks=muted)
        counts = Counter(event for _,_,event,_ in events)
        confirmed = [(i,rs[0]['label']) for i,rs in enumerate(sim['reports'])
                     if len(rs)>=2 and len({r['label'] for r in rs})==1]
        units = sim['units']
        results.append(dict(sent=counts['message_sent'], delivered=counts['message_received'],
                            correct=sum(plan['contacts'][i]['kind']==kind for i,kind in confirmed),
                            incorrect=sum(plan['contacts'][i]['kind']!=kind for i,kind in confirmed),
                            seen=len(sim['seen']), home=sum(u['pos']==HOME and u['role']=='Home' for u in units),
                            spent=sum(plan['battery']-u['energy'] for u in units)))
        traces.append([dict(turn=t,event=e,**d) for _,t,e,d in events
                       if e in ('message_received','message_withheld')])
    return dict(seed=plan['seed'], count=plan['count'], contacts=len(plan['contacts']),
                clear=results[0], muted=results[1], messages=traces)


def make_rounds(seed, phase, count):
    # Each phase has an independent, repeatable stream. Channel choices never
    # change the board, the private samples, or the held-out test set.
    rng = random.Random(f'field-signals-v1/{seed}/{phase}')
    rounds = []
    for _ in range(count):
        truth = [rng.randrange(3) for _ in range(4)]
        local = []
        for i in range(16):
            target = truth[i//4]
            local.append(target if rng.random()<.65 else (target+rng.choice((1,2)))%3)
        noise = [(rng.random(),rng.randrange(3)) for _ in range(48)]
        rounds.append((truth,local,noise))
    return rounds


def inbox(receiver, local, noise, books, channel):
    messages = []
    group = receiver//4*4
    peers = [i for i in range(group,group+4) if i!=receiver]
    for link,sender in enumerate(peers):
        sample, replacement = noise[receiver*3+link]
        if channel=='Muted' or (channel=='Half lost' and sample<.5):
            continue
        token = replacement if channel=='Scrambled' else books[sender][local[sender]]
        messages.append((sender,token))
    return messages


def train(rounds, books, channel):
    # Memory belongs to each listener. Only delivered symbols get feedback.
    memories = [{} for _ in range(16)]
    packets = 0
    for truth,local,noise in rounds:
        for receiver,mem in enumerate(memories):
            messages = inbox(receiver,local,noise,books,channel)
            packets += len(messages)
            for key in messages:
                counts = mem.setdefault(key,[0,0,0])
                counts[truth[receiver//4]]+=1
    return memories, packets


def choose(local, messages, memory):
    votes = [0,0,0]
    votes[local]=1
    decoded = []
    for sender,token in messages:
        evidence = memory.get((sender,token),[0,0,0])
        winner = evidence.index(max(evidence))
        known = sum(evidence)>=3 and evidence.count(max(evidence))==1
        if known:
            votes[winner]+=1
        decoded.append(dict(sender=label(sender), token=token, 
                            decoded=SECTORS[winner] if known else None))
    # Keep the private cue on a tied vote. If two other sectors tie above it,
    # use the first sector in the fixed board order.
    choice = local if votes[local]==max(votes) else votes.index(max(votes))
    return choice, decoded


def evaluate(rounds, books, memories, channel):
    packets=correct=recoveries=0
    scores, decisions = [], []
    for number,(truth,local,noise) in enumerate(rounds,1):
        team_hits=[0]*4
        for receiver in range(16):
            messages=inbox(receiver,local,noise,books,channel)
            choice, decoded=choose(local[receiver],messages,memories[receiver])
            target=truth[receiver//4]
            team_hits[receiver//4]+=int(choice==target)
            packets+=len(messages)
            decisions.append(dict(round=number,unit=label(receiver),cue=SECTORS[local[receiver]],
                                  messages=decoded,choice=SECTORS[choice],truth=SECTORS[target]))
        score=sum(n>=3 for n in team_hits)
        scores.append(score)
        correct+=sum(team_hits)
        recoveries+=score
    return dict(correct=correct,decisions=len(decisions),recoveries=recoveries,
                tasks=4*len(rounds),packets=packets,by_round=scores), decisions


def learning_comparison(seed, link):
    rng=random.Random(f'field-signals-v1/{seed}/codebooks')
    books=[rng.sample(range(3),3) for _ in range(16)]
    training=make_rounds(seed,'train',TRAIN_ROUNDS)
    held_out=make_rounds(seed,'test',TEST_ROUNDS)
    rows, traces=[],[]
    for train_link in ('Clear',link):
        memories, packets=train(training,books,train_link)
        known=accurate=0
        for mem in memories:
            for (sender,token),counts in mem.items():
                if sum(counts)>=3 and counts.count(max(counts))==1:
                    known+=1
                    accurate+=int(books[sender][counts.index(max(counts))]==token)
        for test_link in ('Clear',link):
            row, decisions=evaluate(held_out,books,memories,test_link)
            rows.append(dict(train=train_link,test=test_link,training_packets=packets,known=known,accurate=accurate,**row))
            traces.append(decisions)
    solo,_=evaluate(held_out,books,[{} for _ in range(16)],'Muted')
    # A presenter can inspect both changed and unchanged choices. All trials
    # count toward the score, including trials outside these example pairs.
    changed=[i for i,(a,b) in enumerate(zip(*traces[:2])) if a['choice']!=b['choice']]
    replay=[dict(clear=a,impaired=b) for a,b in zip(*traces[:2])]
    return dict(rows=rows,solo=solo,training_rounds=TRAIN_ROUNDS,test_rounds=TEST_ROUNDS,
                replay=replay,first_change=changed[0] if changed else 0,changed_choices=len(changed))


def experiment(options, current):
    if not isinstance(options,dict) or set(options)!={'seed','link','board'}:
        raise ValueError('Choose a seed, channel and board.')
    seed,link,board=options['seed'],options['link'],options['board']
    if type(seed) is not int or not 0<=seed<=0xffffffff or link not in LINKS or board not in ('Seeded','Planner'):
        raise ValueError('Invalid experiment settings.')
    plan=random_scenario(seed) if board=='Seeded' else current
    return dict(version='field-signals-v1',source='host_simulation',seed=seed,link=link,
                board=board,search_inputs={k:plan[k] for k in ('seed','pattern','cover','count','battery','focus','contacts','custom')},
                mission=mission_comparison(plan),learning=learning_comparison(seed,link))
