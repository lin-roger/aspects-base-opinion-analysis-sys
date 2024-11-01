import re


def score(pred, true):
    correct = 0
    union = []
    union = union + true
    for p in pred:
        if p in true:
            correct += 1
        else:
            union.append(p)

    if len(union) > 0:
        accuracy = correct / len(union)
    else:
        accuracy = 0

    if len(pred) > 0:
        precision = correct / len(pred)
    else:
        precision = 0

    if len(true) > 0:
        recall = correct / len(true)
    else:
        recall = 0

    if (precision + recall) > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0

    return accuracy, precision, recall, f1


def all_score(all_pred, all_true):
    asum, psum, rsum, fsum = 0, 0, 0, 0
    n = len(all_pred)
    for i in range(n):
        pred = all_pred[i]
        true = all_true[i]
        a, p, r, f = score(pred, true)
        asum += a
        psum += p
        rsum += r
        fsum += f
    return asum / n, psum / n, rsum / n, fsum / n


def ans2aop(s):
    tmp = s.split("。")[1:]
    ao_list, aop_list = [], []
    for i in tmp:
        if len(i)==0:
            continue
        
        aop_tmp = i.split("：")
        if len(aop_tmp) == 2:
            a, op = aop_tmp
        else:
            a = "：".join(aop_tmp[:-1])
            op = aop_tmp[-1]
        
        try:
            a = re.search(r"\[.{1,}\]", a).group()[1:-1]
            # print(a)
        except:
            pass
        
        op_list = op.split("、")
        
        for j in op_list:
            o, p = j[:-4], j[-3:-1]
            ao_list.append((a, o))
            aop_list.append((a, o, p))
    
    return (list(set(ao_list)), list(set(aop_list)))
