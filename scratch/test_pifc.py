import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../functions'))
from pvt_exgauss_worker import classify_exgauss_status

def run_tests():
    print("Testing RED (Safety Override)")
    res = classify_exgauss_status(0.5, -2.5, 300)
    assert res['readiness_status'] == 'RED'
    assert 'pifc_protocol' in res
    assert res['pifc_protocol']['title'].startswith('Protocolo Alerta Crítica')
    
    print("Testing ORANGE")
    res = classify_exgauss_status(1.8, -0.5, 300)
    assert res['readiness_status'] == 'ORANGE'
    assert 'pifc_protocol' in res
    
    print("Testing GREEN")
    res = classify_exgauss_status(0.5, 0.5, 250)
    assert res['readiness_status'] == 'GREEN'
    assert 'pifc_protocol' not in res
    
    print("All tests passed!")

if __name__ == '__main__':
    run_tests()
