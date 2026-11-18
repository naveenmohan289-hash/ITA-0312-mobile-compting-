import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"code"))
import common
class Assignment5Tests(unittest.TestCase):
 def job(self,**kw):
  x={"id":"x","arrival":1,"priority":1,"critical":False,"sensitive":False,"encrypted":True,"min_battery":1,"metered_ok":True}; x.update(kw); return x
 def test_sensitive_plaintext_rejected(self):
  m,t=common.schedule([self.job(sensitive=True,encrypted=False)],"fifo",{"battery":90,"network":"good","doze":False,"permission":True})
  self.assertEqual(m["cancelled"],1); self.assertEqual(t[0]["decision"],"unencrypted_sensitive_reject")
 def test_doze_defers_routine_work(self):
  m,_=common.schedule([self.job()],"fifo",{"battery":90,"network":"good","doze":True,"permission":True})
  self.assertEqual(m["deferred"],1)
 def test_permission_revoked_cancels(self):
  m,_=common.schedule([self.job(critical=True)],"fifo",{"battery":90,"network":"good","doze":False,"permission":False})
  self.assertEqual(m["cancelled"],1); self.assertEqual(m["successful"],0)
 def test_exact_enumeration_count(self):
  best,n=common.exact(5,[1,2,3],[1,2]); self.assertEqual(n,6); self.assertIn("cost",best)
 def test_priority_orders_high_first(self):
  items=[self.job(id="low",arrival=1,priority=1),self.job(id="high",arrival=2,priority=5)]
  _,t=common.schedule(items,"priority",{"battery":90,"network":"good","doze":False,"permission":True})
  self.assertEqual(t[0]["id"],"high")
if __name__=="__main__": unittest.main()
