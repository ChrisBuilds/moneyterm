import random
from decimal import Decimal

HEADER = """
OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
 <SIGNONMSGSRSV1>
  <SONRS>
   <STATUS>
    <CODE>0
    <SEVERITY>INFO
   </STATUS>
   <DTSERVER>20230112193422.746
   <LANGUAGE>ENG
   <DTPROFUP>20050531040000.000
   <FI>
    <ORG>TEST_BANK
    <FID>1234
   </FI>
   <INTU.BID>00000
   <INTU.USERID>0123456789
  </SONRS>
 </SIGNONMSGSRSV1>
 <BANKMSGSRSV1>
  <STMTTRNRS>
   <TRNUID>0
   <STATUS>
    <CODE>0
    <SEVERITY>INFO
   </STATUS>
   <STMTRS>
   <CURDEF>USD"""
FOOTER = """
   </STMTRS>
  </STMTTRNRS>
 </BANKMSGSRSV1>
</OFX>"""
BANK = """
<BANKACCTFROM>
 <BANKID>{bankid}
 <ACCTID>{acctid}
 <ACCTTYPE>CHECKING
</BANKACCTFROM>
"""
TX = """
 <STMTTRN>
  <TRNTYPE>POS
  <DTPOSTED>{txdate}
  <TRNAMT>{txamount}
  <FITID>{txid}
  <NAME>{txname}
  <MEMO>{txmemo}
 </STMTTRN>
"""


bankids = set()
acctids = set()
txid = 1
for bank_account in range(1, 4):
    qfx_str = HEADER
    bankid = None
    while not bankid:
        bankid = random.randint(100, 999)
        if bankid in bankids:
            bankid = None
        else:
            bankids.add(bankid)
            break
    acctid = None
    while not acctid:
        acctid = random.randint(1000, 9999)
        if acctid in acctids:
            acctid = None
        else:
            acctids.add(acctid)
            break
    qfx_str += BANK.format(bankid=bankid, acctid=acctid)
    for _ in range(100):
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        year = random.randint(2021, 2023)

        txdate = f"{year}{month:0>2}{day:0>2}000000.000"
        txamount = Decimal(f"{random.randint(-200, -1)}.{random.randint(0, 99)}")
        txname = f"Test Transaction {txid}"
        txmemo = f"{txname} - MEMO"
        tx_str = TX.format(txdate=txdate, txamount=txamount, txid=txid, txname=txname, txmemo=txmemo)
        qfx_str += tx_str
        txid += 1
    qfx_str += FOOTER
    with open(f"test{bank_account}.QFX", "w") as f:
        f.write(qfx_str)
