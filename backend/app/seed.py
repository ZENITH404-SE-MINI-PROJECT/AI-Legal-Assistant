"""Seed data: starter knowledge base, templates and default admin.

Entries are concise summaries for informational use. Admins should verify and
extend them (statutes get amended; e.g. CrPC was replaced by BNSS from 1 July 2024).
"""
import os

from sqlalchemy.orm import Session

from . import security
from .models import CaseReference, Template, User

C = "case"
P = "procedure"

REFERENCES = [
    # ---------- criminal procedure ----------
    dict(entry_type=P, domain="criminal_procedure", title="How to file an FIR",
         keywords="fir,police,complaint,cognizable,zero fir,police station,refuse,register",
         summary="A First Information Report records a cognizable offence. Under the Bharatiya Nagarik "
                 "Suraksha Sanhita (BNSS) 2023, which replaced the CrPC from 1 July 2024, FIR registration "
                 "is covered by Section 173. You may file at any police station (Zero FIR) and are entitled "
                 "to a free copy. If the police refuse, you can send the complaint in writing to the "
                 "Superintendent of Police or approach the Magistrate.",
         steps="Go to the nearest police station (any station can take a Zero FIR) or use the state e-FIR portal.\n"
               "State the facts clearly: date, time, place, persons involved.\nHave it read back, check it, and sign.\n"
               "Insist on a free copy of the FIR.\nIf refused, send the written complaint to the Superintendent of "
               "Police by post or email.\nIf still no action, approach the jurisdictional Magistrate."),
    dict(entry_type=C, domain="criminal_procedure", title="Lalita Kumari v. Government of Uttar Pradesh",
         citation="(2014) 2 SCC 1", keywords="fir,mandatory,cognizable,police,register,preliminary enquiry",
         summary="The Supreme Court held that registration of an FIR is mandatory when the information "
                 "discloses a cognizable offence; a preliminary inquiry is allowed only in limited categories "
                 "(such as matrimonial, commercial or medical negligence disputes, and cases of abnormal delay)."),
    dict(entry_type=C, domain="criminal_procedure", title="D.K. Basu v. State of West Bengal",
         citation="(1997) 1 SCC 416", keywords="arrest,custody,police,detention,rights,guidelines,memo",
         summary="The Supreme Court laid down binding guidelines on arrest and detention: police must carry "
                 "visible identification, prepare an arrest memo attested by a witness, inform a relative or "
                 "friend, and allow a medical examination of the arrestee at regular intervals."),
    dict(entry_type=C, domain="criminal_procedure", title="Arnesh Kumar v. State of Bihar",
         citation="(2014) 8 SCC 273", keywords="arrest,498a,police,magistrate,checklist,bail,unnecessary",
         summary="The Supreme Court directed that police must not arrest automatically in offences punishable "
                 "up to seven years; they should satisfy the statutory necessity checklist, and magistrates "
                 "must examine it before authorising detention."),
    dict(entry_type=C, domain="criminal_procedure", title="Maneka Gandhi v. Union of India",
         citation="AIR 1978 SC 597", keywords="article 21,personal liberty,fair procedure,due process,passport",
         summary="The Supreme Court held that any law depriving a person of personal liberty under Article 21 "
                 "must follow a procedure that is fair, just and reasonable, linking Articles 14, 19 and 21."),
    # ---------- consumer ----------
    dict(entry_type=P, domain="consumer", title="How to file a consumer complaint",
         keywords="consumer,complaint,refund,defective,deficiency,seller,e-daakhil,commission,court,forum",
         summary="Under the Consumer Protection Act, 2019 you can complain about defective goods or deficient "
                 "services. Complaints go to the District, State or National Commission depending on the value "
                 "of goods or services paid. No court fee applies for claims up to Rs 5 lakh, and complaints "
                 "can be filed online through the e-Daakhil portal. The limitation period is two years from "
                 "the cause of action.",
         steps="Collect invoice, warranty, photos and all communication with the seller.\n"
               "Send a written legal notice or complaint to the seller giving a reasonable deadline.\n"
               "If unresolved, file the complaint on e-Daakhil (or in person) before the appropriate Commission.\n"
               "Attach documents and state the relief sought (refund, replacement, compensation).\n"
               "Attend hearings; the Commission may refer to mediation."),
    dict(entry_type=C, domain="consumer", title="Lucknow Development Authority v. M.K. Gupta",
         citation="(1994) 1 SCC 243", keywords="consumer,service,deficiency,compensation,authority,housing",
         summary="The Supreme Court held that statutory authorities providing services such as housing are "
                 "covered by consumer law, and that harassment of a consumer through deficient service can "
                 "attract compensation."),
    dict(entry_type=C, domain="consumer", title="Indian Medical Association v. V.P. Shantha",
         citation="(1995) 6 SCC 651", keywords="consumer,medical,doctor,hospital,negligence,service",
         summary="The Supreme Court held that medical services rendered for a fee fall within the scope of "
                 "'service' under the Consumer Protection Act, making deficiency in medical service actionable "
                 "before consumer forums."),
    # ---------- tenancy ----------
    dict(entry_type=P, domain="tenancy", title="Rent agreements and security deposit basics",
         keywords="rent,agreement,lease,tenant,landlord,deposit,security deposit,registration,stamp,leave and license",
         summary="Tenancy is governed mainly by the Transfer of Property Act, 1882 and state rent laws. A lease "
                 "of more than 11 months generally must be registered under the Registration Act, 1908, and "
                 "stamp duty is state-specific. Security deposit limits and return timelines vary by state; "
                 "always get a written agreement and a receipt.",
         steps="Put the agreement in writing: parties, rent, deposit, duration, notice period, repair duties.\n"
               "Pay stamp duty as per your state; register if the term exceeds 11 months.\n"
               "Take dated photos of the property condition at move-in.\nPay rent by traceable means and keep receipts.\n"
               "At move-out, request a joint inspection and written confirmation of deposit refund."),
    dict(entry_type=P, domain="tenancy", title="Eviction and notice to a tenant",
         keywords="eviction,evict,notice,tenant,landlord,vacate,month to month,tenancy,rent control",
         summary="A landlord cannot lawfully evict a tenant by force or by cutting essential services. For a "
                 "month-to-month tenancy, Section 106 of the Transfer of Property Act requires 15 days' written "
                 "notice, and state rent-control laws may add grounds and procedures. Disputes go to the rent "
                 "controller or civil court.",
         steps="Landlord serves a written notice stating the ground and the notice period.\n"
               "If the tenant does not vacate, the landlord files an eviction petition before the competent authority.\n"
               "Tenant may contest the petition and may deposit disputed rent as the law requires.\n"
               "Only a court or authority order can be enforced to recover possession."),
    dict(entry_type=C, domain="tenancy", title="Satyawati Sharma v. Union of India",
         citation="(2008) 5 SCC 287", keywords="tenant,landlord,eviction,bona fide need,rent control,article 14",
         summary="The Supreme Court held that a provision of the Delhi Rent Control Act that treated landlords "
                 "needing residential and commercial premises differently was unreasonable and violated "
                 "Article 14 to that extent."),
    # ---------- family ----------
    dict(entry_type=P, domain="family", title="Divorce by mutual consent",
         keywords="divorce,mutual consent,marriage,separation,hindu marriage act,13b,petition,cooling off",
         summary="Under Section 13B of the Hindu Marriage Act, 1955 spouses may jointly petition for divorce "
                 "after living apart for at least one year. The law provides a six-month waiting period before "
                 "the second motion, which courts may waive in suitable cases. Other personal laws and the "
                 "Special Marriage Act have similar provisions.",
         steps="Confirm one year of separation and that both spouses genuinely consent.\n"
               "File a joint petition in the Family Court with the marriage details and settlement terms.\n"
               "Both spouses appear; statements are recorded (first motion).\n"
               "After the waiting period (waivable), file the second motion and appear again.\n"
               "The court passes the decree of divorce."),
    dict(entry_type=C, domain="family", title="Amardeep Singh v. Harveen Kaur",
         citation="(2017) 8 SCC 746", keywords="divorce,mutual consent,cooling off,six months,waiver,13b",
         summary="The Supreme Court held that the six-month waiting period in Section 13B(2) is directory, "
                 "not mandatory, and may be waived by the Family Court where reconciliation is impossible and "
                 "settlement terms are in place."),
    dict(entry_type=C, domain="family", title="Rajnesh v. Neha",
         citation="(2021) 2 SCC 324", keywords="maintenance,alimony,wife,affidavit,disclosure,interim,husband",
         summary="The Supreme Court issued uniform guidelines on maintenance: both parties must file an "
                 "affidavit of assets and liabilities, courts should consider relevant factors, and maintenance "
                 "is generally payable from the date of the application."),
    dict(entry_type=P, domain="family", title="Seeking help under the Domestic Violence Act",
         keywords="domestic violence,husband,wife,abuse,protection order,dowry,harassment,protection officer",
         summary="The Protection of Women from Domestic Violence Act, 2005 lets an aggrieved woman seek "
                 "protection orders, residence orders and monetary relief from a Magistrate, with help from "
                 "a Protection Officer. The National Commission for Women and the 181 helpline can assist.",
         steps="In an emergency call 112; the Women Helpline 181 can also assist.\n"
               "Contact a Protection Officer, service provider (shelter/NGO) or the police.\n"
               "File an application before the Magistrate for protection/residence/monetary relief.\n"
               "The Magistrate may pass interim orders; keep records of incidents and medical reports."),
    # ---------- employment ----------
    dict(entry_type=P, domain="employment", title="Gratuity eligibility and calculation",
         keywords="gratuity,employee,employer,salary,resignation,five years,retirement,payment of gratuity act",
         summary="Under the Payment of Gratuity Act, 1972, an employee generally becomes eligible after five "
                 "years of continuous service (exceptions include death or disablement). Gratuity is "
                 "calculated as last drawn monthly wages x 15/26 x completed years of service. Rules may be "
                 "affected by the new labour codes, so verify current provisions.",
         steps="Check you have completed five years of continuous service.\n"
               "Submit a written application (Form I) to the employer within 30 days of becoming payable.\n"
               "Employer must determine and pay within 30 days; delay attracts interest.\n"
               "If denied or delayed, approach the Controlling Authority under the Act."),
    dict(entry_type=P, domain="employment", title="Unpaid salary or wrongful termination",
         keywords="salary,wages,unpaid,termination,fired,employer,notice period,labour,dues,layoff",
         summary="If wages are unpaid or you are terminated without following your contract or applicable "
                 "law, first raise the issue in writing with the employer. You may then approach the Labour "
                 "Commissioner or Labour Court. Industrial workers are protected by the Industrial Disputes "
                 "Act (now being consolidated in the Industrial Relations Code), and white-collar employees "
                 "can also pursue civil remedies for breach of contract.",
         steps="Collect appointment letter, payslips, bank statements and emails.\n"
               "Send a written demand or legal notice with a clear deadline.\n"
               "File a complaint with the Labour Commissioner/Labour Office of your area.\n"
               "If conciliation fails the matter may be referred to the Labour Court or Tribunal."),
    dict(entry_type=C, domain="employment", title="Vishaka v. State of Rajasthan",
         citation="AIR 1997 SC 3011", keywords="sexual harassment,workplace,posh,guidelines,women,harassment,employer",
         summary="The Supreme Court laid down guidelines to prevent sexual harassment at the workplace, later "
                 "codified in the Sexual Harassment of Women at Workplace (Prevention, Prohibition and "
                 "Redressal) Act, 2013, which requires an Internal Committee in workplaces with 10 or more employees."),
    # ---------- cyber ----------
    dict(entry_type=P, domain="cyber", title="Reporting online financial fraud",
         keywords="cyber,fraud,upi,otp,scam,phishing,online fraud,bank,money,hacked,report,1930",
         summary="For online financial fraud, act immediately: call the national cybercrime helpline 1930 and "
                 "report on cybercrime.gov.in. Inform your bank at once to block cards or accounts. The "
                 "Information Technology Act, 2000 (for example Sections 66C and 66D on identity theft and "
                 "cheating by personation) and criminal law provisions may apply.",
         steps="Call 1930 right away; the sooner the report, the better the chance of freezing funds.\n"
               "Report on cybercrime.gov.in with transaction IDs, screenshots, phone numbers and UPI IDs.\n"
               "Contact your bank to block the card/account and request a dispute.\n"
               "File a written complaint or FIR at the local cyber police station if directed.\n"
               "Change passwords and enable two-factor authentication."),
    dict(entry_type=C, domain="cyber", title="Shreya Singhal v. Union of India",
         citation="(2015) 5 SCC 1", keywords="66a,it act,free speech,online,social media,cyber,article 19",
         summary="The Supreme Court struck down Section 66A of the Information Technology Act, 2000 as "
                 "unconstitutional for violating freedom of speech under Article 19(1)(a), and read down "
                 "the intermediary takedown rules."),
    dict(entry_type=C, domain="cyber", title="K.S. Puttaswamy v. Union of India",
         citation="(2017) 10 SCC 1", keywords="privacy,fundamental right,data,aadhaar,article 21,data breach",
         summary="A nine-judge Constitution Bench of the Supreme Court unanimously held that the right to "
                 "privacy is a fundamental right under Article 21 and part of the freedoms guaranteed by Part III."),
    # ---------- RTI ----------
    dict(entry_type=P, domain="rti", title="How to file an RTI application",
         keywords="rti,right to information,pio,application,fee,first appeal,information commission,government",
         summary="The Right to Information Act, 2005 lets any citizen request information from a public "
                 "authority by writing to its Public Information Officer (PIO). The central fee is Rs 10; "
                 "states may differ. The PIO must reply within 30 days (48 hours where life or liberty is "
                 "involved). If unsatisfied, file a first appeal within 30 days and then a second appeal to "
                 "the Information Commission within 90 days.",
         steps="Identify the public authority and its PIO (or use the RTI Online portal for central bodies).\n"
               "Write the application stating exactly what information you want; pay the prescribed fee.\n"
               "Keep the acknowledgement; the PIO must reply within 30 days.\n"
               "If no reply or unsatisfactory, file a first appeal with the First Appellate Authority within 30 days.\n"
               "Still unsatisfied: second appeal to the Central/State Information Commission within 90 days."),
]

TEMPLATES = [
    dict(title="Leave and Licence (Rent) Agreement", category="tenancy",
         description="Basic residential rent agreement draft.",
         body="LEAVE AND LICENCE AGREEMENT\n\nThis agreement is made on {{agreement_date}} between {{landlord_name}} "
              "(Licensor) residing at {{landlord_address}} and {{tenant_name}} (Licensee) residing at "
              "{{tenant_address}}.\n\n1. The Licensor permits the Licensee to occupy the premises at {{property_address}} "
              "for {{duration_months}} months starting {{start_date}}.\n2. Monthly rent is Rs {{monthly_rent}}, payable by "
              "the {{due_day}} of each month.\n3. A refundable security deposit of Rs {{security_deposit}} is paid and "
              "will be returned within 30 days of vacating, less lawful deductions.\n4. Either party may terminate by "
              "giving {{notice_days}} days' written notice.\n\nSigned: {{landlord_name}} (Licensor)    {{tenant_name}} (Licensee)\n\n"
              "Note: draft for general use. Check stamp duty and registration rules of your state and get it reviewed."),
    dict(title="Consumer Complaint Notice", category="consumer",
         description="Notice to a seller/service provider before approaching the Consumer Commission.",
         body="To,\n{{seller_name}}\n{{seller_address}}\n\nDate: {{date}}\n\nSubject: Notice regarding {{product_or_service}}\n\n"
              "Sir/Madam,\n\nI purchased {{product_or_service}} on {{purchase_date}} for Rs {{amount_paid}} "
              "(Invoice/Order No. {{invoice_number}}). The issue is: {{issue_description}}.\n\n"
              "I request that you {{relief_sought}} within {{deadline_days}} days of receiving this notice, failing which "
              "I will approach the appropriate Consumer Disputes Redressal Commission under the Consumer Protection Act, 2019.\n\n"
              "Yours faithfully,\n{{customer_name}}\n{{customer_contact}}"),
    dict(title="RTI Application", category="rti",
         description="Request for information under the RTI Act, 2005.",
         body="To,\nThe Public Information Officer,\n{{public_authority}}\n{{authority_address}}\n\nDate: {{date}}\n\n"
              "Subject: Request for information under the Right to Information Act, 2005\n\nSir/Madam,\n\n"
              "Under Section 6(1) of the RTI Act, 2005, please provide the following information for the period "
              "{{period}}:\n\n{{information_sought}}\n\nI am a citizen of India. I am enclosing the application fee of "
              "Rs {{fee}} by {{fee_mode}}.\n\nYours faithfully,\n{{applicant_name}}\n{{applicant_address}}"),
    dict(title="Cyber Crime Complaint Letter", category="cyber",
         description="Written complaint to the cyber crime police for online fraud.",
         body="To,\nThe Station House Officer,\nCyber Crime Police Station, {{city}}\n\nDate: {{date}}\n\n"
              "Subject: Complaint regarding online fraud\n\nSir/Madam,\n\nOn {{incident_date}} I was defrauded of "
              "Rs {{amount_lost}} through {{method_of_fraud}}. Transaction details: {{transaction_details}}. "
              "I reported the incident on the National Cyber Crime Reporting Portal (acknowledgement no. "
              "{{portal_ack_number}}).\n\nI request that an FIR be registered and the matter investigated.\n\n"
              "Yours faithfully,\n{{complainant_name}}\n{{complainant_contact}}"),
    dict(title="Legal Notice for Unpaid Salary", category="employment",
         description="Demand notice to an employer for unpaid wages.",
         body="To,\n{{employer_name}}\n{{employer_address}}\n\nDate: {{date}}\n\nSubject: Notice for payment of unpaid salary\n\n"
              "Sir/Madam,\n\nI have been employed with you as {{designation}} since {{joining_date}}. Salary of "
              "Rs {{amount_due}} for {{months_due}} remains unpaid despite repeated requests.\n\n"
              "Please clear the dues within {{deadline_days}} days of this notice, failing which I will approach the "
              "Labour Commissioner and other competent authorities at your risk and cost.\n\n"
              "Yours faithfully,\n{{employee_name}}\n{{employee_contact}}"),
]


def seed(db: Session) -> None:
    if db.query(CaseReference).count() == 0:
        db.add_all(CaseReference(**r) for r in REFERENCES)
    if db.query(Template).count() == 0:
        db.add_all(Template(**t) for t in TEMPLATES)
    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if admin_user and admin_pass and not db.query(User).filter(User.username == admin_user).first():
        db.add(User(username=admin_user, password_hash=security.hash_password(admin_pass), role="admin"))
    db.commit()
