import os,tempfile,unittest
os.environ['LOCALAPPDATA']=tempfile.mkdtemp()
from mt5_bridge import summarize

def deal(ticket,entry,volume,price,profit=0,reason=0):return dict(ticket=ticket,time=ticket,position_id=7,type=0 if entry==0 else 1,entry=entry,volume=volume,price=price,profit=profit,commission=-.1,swap=0,fee=0,symbol='XAUUSD',magic=99,comment='PUCUK',reason=reason)
class Tests(unittest.TestCase):
 def test_partial_closed(self):
  t=summarize([deal(1,0,1,100),deal(2,1,.4,110,4),deal(3,1,.6,110,6,5)],[])[0]
  self.assertEqual(t['status'],'CLOSED');self.assertAlmostEqual(t['net'],9.7);self.assertEqual(t['reason'],'TP broker');self.assertEqual(t['exit'],110)
 def test_partial_open(self):
  t=summarize([deal(1,0,1,100),deal(2,1,.4,110,4)],[dict(ticket=7,identifier=7)])[0];self.assertEqual(t['status'],'OPEN')
 def test_reversal_review(self):
  self.assertEqual(summarize([deal(1,0,1,100),deal(2,2,2,110)],[])[0]['status'],'REVIEW')
 def test_incomplete_review(self):
  self.assertEqual(summarize([deal(1,0,1,100),deal(2,1,.4,110)],[])[0]['status'],'REVIEW')
 def test_duplicate_snapshot(self):
  ds=[deal(1,0,1,100),deal(2,1,1,90,-10,4)];self.assertEqual(summarize(ds,[]),summarize(ds,[]));self.assertEqual(len(summarize(ds,[])),1)
 def test_balance_excluded(self):self.assertEqual(summarize([dict(position_id=0,type=2)],[]),[])
if __name__=='__main__':unittest.main()
