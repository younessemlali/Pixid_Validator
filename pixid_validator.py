import streamlit as st
import xml.etree.ElementTree as ET
from lxml import etree
import re
import csv
import io
from datetime import datetime, date
from collections import defaultdict

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Pixid XML Validator",
    page_icon="🔍",
    layout="wide"
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface2: #1a1a24;
    --border: #2a2a3a;
    --accent: #00e5ff;
    --accent2: #ff3d71;
    --warn: #ffaa00;
    --ok: #00e096;
    --text: #e8e8f0;
    --muted: #6b6b8a;
}

* { font-family: 'Syne', sans-serif; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background: var(--bg); color: var(--text); }

.validator-header {
    background: linear-gradient(135deg, #0a0a0f 0%, #111128 100%);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.validator-header::before {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,229,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.validator-header h1 {
    font-size: 2rem; font-weight: 800;
    color: var(--text); margin: 0 0 0.3rem 0;
    letter-spacing: -0.02em;
}
.validator-header .subtitle { color: var(--muted); font-size: 0.9rem; }
.version-badge {
    display: inline-block;
    background: rgba(0,229,255,0.1);
    color: var(--accent);
    border: 1px solid rgba(0,229,255,0.3);
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    margin-left: 1rem; vertical-align: middle;
}

.score-card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.score-number {
    font-size: 2.8rem; font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1; margin-bottom: 0.3rem;
}
.score-label {
    font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.15em; color: var(--muted);
}

.check-item {
    background: var(--surface2);
    border-left: 3px solid;
    padding: 0.6rem 1rem;
    margin: 0.3rem 0;
    font-size: 0.82rem;
}
.check-item.error { border-color: var(--accent2); background: rgba(255,61,113,0.05); }
.check-item.warning { border-color: var(--warn); background: rgba(255,170,0,0.05); }
.check-item.ok { border-color: var(--ok); background: rgba(0,224,150,0.04); }

.tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; padding: 0.1rem 0.4rem;
    margin-right: 0.5rem; font-weight: 700;
}
.tag-error { background: var(--accent2); color: #fff; }
.tag-warn { background: var(--warn); color: #000; }
.tag-ok { background: var(--ok); color: #000; }

.section-title {
    font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.2em; color: var(--muted);
    margin: 1.2rem 0 0.5rem 0;
    display: flex; align-items: center; gap: 0.5rem;
}
.section-title::after {
    content: ''; flex: 1; height: 1px;
    background: var(--border);
}

.summary-table {
    width: 100%; border-collapse: collapse;
    font-size: 0.82rem;
}
.summary-table th {
    background: var(--surface2);
    color: var(--muted); font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    font-size: 0.68rem; padding: 0.6rem 1rem;
    border-bottom: 1px solid var(--border);
    text-align: left;
}
.summary-table td {
    padding: 0.6rem 1rem;
    border-bottom: 1px solid rgba(42,42,58,0.5);
    font-family: 'JetBrains Mono', monospace;
}
.summary-table tr:hover td { background: var(--surface2); }

.status-ok { color: var(--ok); font-weight: 700; }
.status-warn { color: var(--warn); font-weight: 700; }
.status-error { color: var(--accent2); font-weight: 700; }

.verdict-box {
    margin-top: 1.5rem;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 4px solid;
    padding: 1.5rem 2rem;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

.stButton > button {
    background: var(--accent) !important;
    color: #000 !important; border: none !important;
    border-radius: 0 !important; font-weight: 700 !important;
    font-family: 'Syne', sans-serif !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
}
.stButton > button:hover { background: #00b8d4 !important; }

.stFileUploader > div {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 0 !important;
}
.stFileUploader > div:hover { border-color: var(--accent) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def find_in_subtree(elem, tag):
    results = []
    for ns_uri in ['http://ns.hr-xml.org/2004-08-02', '']:
        t = f'{{{ns_uri}}}{tag}' if ns_uri else tag
        results.extend(elem.iter(t))
    seen = set()
    unique = []
    for r in results:
        if id(r) not in seen:
            seen.add(id(r))
            unique.append(r)
    return unique

def get_text(elem):
    if elem is None: return None
    return (elem.text or '').strip()

def get_contract_number(assignment):
    for tag in ['AssignmentId', 'ContractId']:
        elems = find_in_subtree(assignment, tag)
        if elems:
            idvals = find_in_subtree(elems[0], 'IdValue')
            if idvals:
                val = get_text(idvals[0])
                if val:
                    return val
    return None

def detect_file_type(root):
    xml_str = ET.tostring(root, encoding='unicode')[:3000]
    if 'Invoice' in xml_str or 'TotalCharges' in xml_str:
        return 'facture'
    if 'AssignmentPacket' in xml_str or 'Assignment' in xml_str:
        return 'contrat'
    if 'TimeCardPacket' in xml_str or 'TimeCard' in xml_str:
        return 'ra_rcv'
    if 'OrderPacket' in xml_str or 'StaffingOrder' in xml_str:
        return 'commande'
    return 'inconnu'

# ─────────────────────────────────────────────
# CLASSES RÉSULTATS
# ─────────────────────────────────────────────

class GlobalResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.ok = []
    def error(self, msg, detail=""):
        self.errors.append({"msg": msg, "detail": detail})
    def warn(self, msg, detail=""):
        self.warnings.append({"msg": msg, "detail": detail})
    def success(self, msg):
        self.ok.append({"msg": msg})

class ContractResult:
    def __init__(self, contract_num, index):
        self.contract_num = contract_num or f"Inconnu #{index}"
        self.index = index
        self.errors = []
        self.warnings = []
        self.ok = []
    def error(self, msg, detail=""):
        self.errors.append({"msg": msg, "detail": detail})
    def warn(self, msg, detail=""):
        self.warnings.append({"msg": msg, "detail": detail})
    def success(self, msg):
        self.ok.append({"msg": msg})
    @property
    def status(self):
        if self.errors: return "error"
        if self.warnings: return "warning"
        return "ok"
    @property
    def status_label(self):
        if self.errors: return "❌ ERREUR"
        if self.warnings: return "⚠️ ATTENTION"
        return "✅ CONFORME"
    @property
    def score(self):
        total = len(self.errors) + len(self.warnings) + len(self.ok)
        if total == 0: return 100
        return int(((len(self.ok) + len(self.warnings) * 0.5) / total) * 100)

# ─────────────────────────────────────────────
# VALIDATION SYNTAXE XML
# ─────────────────────────────────────────────

def validate_syntax(content_bytes):
    r = GlobalResult()

    # Encodage
    try:
        header = content_bytes[:200].decode('ascii', errors='replace')
        enc_match = re.search(r'encoding=["\']([^"\']+)["\']', header, re.IGNORECASE)
        declared_enc = enc_match.group(1).upper() if enc_match else None

        if declared_enc:
            if declared_enc in ['UTF-8', 'ISO-8859-1', 'ISO-8859-15']:
                r.success(f"Encodage déclaré valide : {declared_enc}")
            else:
                r.error(f"Encodage non accepté par Pixid : {declared_enc}",
                        "Valeurs acceptées : UTF-8, ISO-8859-1, ISO-8859-15")
        else:
            r.warn("Aucun encodage déclaré en entête XML")

        enc_to_test = 'iso-8859-1' if declared_enc in ['ISO-8859-1', 'ISO-8859-15'] else 'utf-8'
        try:
            content_bytes.decode(enc_to_test)
            r.success(f"Contenu décodable en {enc_to_test.upper()}")
        except UnicodeDecodeError as e:
            r.error("Incohérence encodage déclaré vs contenu réel", str(e))
    except Exception as e:
        r.error("Impossible d'analyser l'entête", str(e))

    # XML bien formé
    try:
        parser = etree.XMLParser(recover=False)
        etree.fromstring(content_bytes, parser)
        r.success("XML bien formé (balises ouvertes/fermées correctement)")
    except etree.XMLSyntaxError as e:
        msg = str(e)
        line_match = re.search(r'line (\d+)', msg)
        line_info = f" (ligne {line_match.group(1)})" if line_match else ""
        r.error(f"XML mal formé{line_info}", msg)
        return r, False

    # Caractères interdits
    try:
        text = content_bytes.decode('iso-8859-1', errors='replace')
        forbidden = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text)
        if forbidden:
            r.error(f"Caractères de contrôle interdits ({len(forbidden)} occurrence(s))")
        else:
            r.success("Aucun caractère de contrôle interdit")

        bad_entities = re.findall(
            r'&(?!amp;|lt;|gt;|apos;|quot;|#\d+;|#x[0-9a-fA-F]+;)[a-zA-Z][a-zA-Z0-9]*;', text)
        if bad_entities:
            r.error(f"Entités XML non définies : {set(bad_entities)}")
        else:
            r.success("Aucune entité XML non définie")
    except:
        pass

    # Namespace HR-XML
    try:
        text = content_bytes.decode('iso-8859-1', errors='replace')
        if 'http://ns.hr-xml.org/2004-08-02' in text:
            r.success("Namespace HR-XML SIDES déclaré")
        else:
            r.warn("Namespace HR-XML SIDES absent")
    except:
        pass

    return r, True

# ─────────────────────────────────────────────
# VALIDATION PAR CONTRAT
# ─────────────────────────────────────────────

def validate_single_contract(assignment, index):
    contract_num = get_contract_number(assignment)
    r = ContractResult(contract_num, index)

    # ── AssignmentId ──
    aid_elems = find_in_subtree(assignment, 'AssignmentId')
    if not aid_elems:
        r.error("AssignmentId absent (obligatoire)")
    else:
        owner = aid_elems[0].get('idOwner', '')
        if not owner:
            r.error("AssignmentId sans attribut idOwner")
        else:
            r.success(f"AssignmentId présent — idOwner='{owner}'")
        idvals = find_in_subtree(aid_elems[0], 'IdValue')
        if not idvals or not get_text(idvals[0]):
            r.error("AssignmentId/IdValue vide")

    # ── ReferenceInformation ──
    refs = find_in_subtree(assignment, 'ReferenceInformation')
    if not refs:
        r.error("ReferenceInformation absent (obligatoire)")
    else:
        ref = refs[0]
        r.success("ReferenceInformation présent")
        for req_tag in ['StaffingCustomerId', 'StaffingCustomerOrgUnitId']:
            elems = find_in_subtree(ref, req_tag)
            if not elems:
                r.error(f"{req_tag} absent dans ReferenceInformation")
            else:
                owner = elems[0].get('idOwner', '')
                if not owner:
                    r.error(f"{req_tag} sans idOwner")
                else:
                    r.success(f"{req_tag} présent — idOwner='{owner}'")
                idvals = find_in_subtree(elems[0], 'IdValue')
                if not idvals or not get_text(idvals[0]):
                    r.error(f"{req_tag}/IdValue vide")

    # ── CustomerReportingRequirements ──
    crrs = find_in_subtree(assignment, 'CustomerReportingRequirements')
    if not crrs:
        r.error("CustomerReportingRequirements absent (obligatoire)")
    else:
        crr = crrs[0]
        r.success("CustomerReportingRequirements présent")
        cc_code = find_in_subtree(crr, 'CostCenterCode')
        cc_name = find_in_subtree(crr, 'CostCenterName')
        if cc_code and not cc_name:
            r.warn("CostCenterCode présent mais CostCenterName absent")
        elif cc_name and not cc_code:
            r.warn("CostCenterName présent mais CostCenterCode absent")
        elif cc_code and cc_name:
            r.success(f"CostCenter OK — Code='{get_text(cc_code[0])}'")

    # ── Rates ──
    rates = find_in_subtree(assignment, 'Rates')
    if not rates:
        r.error("Aucun groupe <Rates> (obligatoire)")
    else:
        r.success(f"{len(rates)} groupe(s) Rates")
        taux_zero = []
        for ri, rate in enumerate(rates):
            rtype = rate.get('rateType', '')
            rstatus = rate.get('rateStatus', '')
            if rtype not in ['bill', 'pay']:
                r.error(f"Rates#{ri+1} : rateType='{rtype}' invalide (bill/pay attendu)")
            if rstatus not in ['proposed', 'agreed']:
                r.warn(f"Rates#{ri+1} : rateStatus='{rstatus}' (proposed/agreed attendu)")
            amounts = find_in_subtree(rate, 'Amount')
            for amt in amounts:
                val = get_text(amt)
                if val in ['0', '0.0', '0.00', '0,00']:
                    taux_zero.append(ri + 1)
        if taux_zero:
            r.warn(f"Taux à 0 détecté dans Rates#{taux_zero}")

        found_100010 = False
        for rate in rates:
            for child in rate.iter():
                local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if local in ['RatesId', 'IdValue']:
                    if child.get('idValue') == '100010' or get_text(child) == '100010':
                        found_100010 = True
        if found_100010:
            r.success("RatesId '100010' (taux horaire de base) présent")
        else:
            r.warn("RatesId '100010' non trouvé — vérifier la codification")

        bm_elems = find_in_subtree(assignment, 'BillingMultiplier')
        if bm_elems:
            for bm in bm_elems:
                if bm.get('percentIndicator') != 'true':
                    r.warn("BillingMultiplier sans percentIndicator='true'")
                else:
                    r.success("BillingMultiplier percentIndicator='true' ✓")
                val = get_text(bm)
                if val in ['0', '0.0', '0.00', '1', '1.0']:
                    r.warn(f"BillingMultiplier='{val}' — vérifier que le coefficient est correct")
        else:
            r.warn("BillingMultiplier absent dans les Rates")

    # ── StaffingShift ──
    shifts = find_in_subtree(assignment, 'StaffingShift')
    if not shifts:
        r.error("StaffingShift absent (obligatoire)")
    else:
        weekly = [s for s in shifts if s.get('shiftPeriod') == 'weekly']
        if len(weekly) == 0:
            r.error("Aucun StaffingShift avec shiftPeriod='weekly'")
        elif len(weekly) > 1:
            r.error(f"{len(weekly)} blocs StaffingShift weekly — un seul autorisé (erreur INT300)")
        else:
            r.success("StaffingShift weekly unique ✓")
        for s in shifts:
            for id_elem in find_in_subtree(s, 'Id'):
                owner = id_elem.get('idOwner', '')
                if owner != 'EXT0':
                    r.warn(f"StaffingShift/Id idOwner='{owner}' (EXT0 attendu)")
                for iv in find_in_subtree(id_elem, 'IdValue'):
                    name_attr = iv.get('name', '')
                    if name_attr and name_attr not in ['MODELE', 'CYCLE']:
                        r.warn(f"StaffingShift IdValue name='{name_attr}' inconnu (MODELE/CYCLE attendu)")

    # ── AssignmentDateRange ──
    dates = find_in_subtree(assignment, 'AssignmentDateRange')
    if not dates:
        r.error("AssignmentDateRange absent (obligatoire)")
    else:
        dr = dates[0]
        start_elems = find_in_subtree(dr, 'StartDate') + find_in_subtree(dr, 'StartDateTime')
        end_elems = find_in_subtree(dr, 'EndDate') + find_in_subtree(dr, 'EndDateTime')
        start_str = get_text(start_elems[0]) if start_elems else None
        end_str = get_text(end_elems[0]) if end_elems else None

        if not start_str:
            r.error("StartDate absent dans AssignmentDateRange")
        elif not re.match(r'^\d{4}-\d{2}-\d{2}', start_str):
            r.error(f"Format StartDate invalide : '{start_str}' (yyyy-mm-dd attendu)")
        else:
            r.success(f"StartDate : {start_str[:10]}")

        if not end_str:
            r.warn("EndDate absent dans AssignmentDateRange")
        elif not re.match(r'^\d{4}-\d{2}-\d{2}', end_str):
            r.error(f"Format EndDate invalide : '{end_str}' (yyyy-mm-dd attendu)")
        else:
            r.success(f"EndDate : {end_str[:10]}")
            try:
                end_date = datetime.strptime(end_str[:10], '%Y-%m-%d').date()
                if end_date < date.today():
                    r.warn(f"Contrat expiré — date de fin {end_str[:10]} est dans le passé")
            except:
                pass

        if start_str and end_str:
            try:
                if start_str[:10] > end_str[:10]:
                    r.error(f"Date début ({start_str[:10]}) > Date fin ({end_str[:10]})")
                else:
                    r.success(f"Cohérence dates ✓ ({start_str[:10]} → {end_str[:10]})")
            except:
                pass

    # ── ContractInformation ──
    ci_elems = find_in_subtree(assignment, 'ContractInformation')
    if not ci_elems:
        r.error("ContractInformation absent (obligatoire)")
    else:
        ci = ci_elems[0]
        ct = ci.get('contractType', '')
        cs = ci.get('contractStatus', '')

        if ct != 'staffing customer':
            r.error(f"contractType='{ct}' invalide (valeur fixe: 'staffing customer')")
        else:
            r.success("contractType='staffing customer' ✓")

        if cs != 'unsigned':
            r.warn(f"contractStatus='{cs}' (attendu 'unsigned' pour création)")
        else:
            r.success("contractStatus='unsigned' ✓")

        # ContractId
        cid_elems = find_in_subtree(ci, 'ContractId')
        if not cid_elems:
            r.error("ContractId absent dans ContractInformation")
        else:
            cid_owner = cid_elems[0].get('idOwner', '')
            aid_owner = ''
            aid_elems2 = find_in_subtree(assignment, 'AssignmentId')
            if aid_elems2:
                aid_owner = aid_elems2[0].get('idOwner', '')
            if not cid_owner:
                r.error("ContractId sans idOwner")
            elif cid_owner != aid_owner and aid_owner:
                r.warn(f"idOwner ContractId='{cid_owner}' ≠ AssignmentId='{aid_owner}'")
            else:
                r.success(f"ContractId idOwner='{cid_owner}' cohérent avec AssignmentId")
            idvals = find_in_subtree(cid_elems[0], 'IdValue')
            if not idvals or not get_text(idvals[0]):
                r.error("ContractId/IdValue vide")

        # ContractVersion
        cv_elems = find_in_subtree(ci, 'ContractVersion')
        if not cv_elems:
            r.error("ContractVersion absent (obligatoire)")
        else:
            cv = get_text(cv_elems[0])
            if cv and not re.match(r'^\d{2}$', cv):
                r.error(f"ContractVersion='{cv}' invalide (2 chiffres: '00', '01'...)")
            else:
                r.success(f"ContractVersion='{cv}' ✓")

        # StaffType
        st_elems = find_in_subtree(ci, 'StaffType')
        if not st_elems:
            r.error("StaffType absent (obligatoire)")
        else:
            st_val = get_text(st_elems[0])
            if st_val != 'temporary employee':
                r.error(f"StaffType='{st_val}' invalide (valeur fixe: 'temporary employee')")
            else:
                r.success("StaffType='temporary employee' ✓")

        # LocalContractRequirements
        lcr = find_in_subtree(ci, 'LocalContractRequirements')
        if not lcr:
            r.error("LocalContractRequirements absent (obligatoire)")
        else:
            r.success("LocalContractRequirements présent")
            lct_elems = find_in_subtree(lcr[0], 'LocalContractType')
            if lct_elems:
                lct_val = get_text(lct_elems[0])
                if not re.match(r'^(DDF|DDE|DMF|DME)', lct_val or ''):
                    r.error(f"LocalContractType='{lct_val}' invalide (DDF/DDE/DMF/DME attendu en préfixe)")
                else:
                    r.success(f"LocalContractType='{lct_val}' ✓")

    # ── Cohérence AssignmentId == ContractId (valeurs) ──
    aid_elems3 = find_in_subtree(assignment, 'AssignmentId')
    cid_elems2 = find_in_subtree(assignment, 'ContractId')
    if aid_elems3 and cid_elems2:
        aid_idval = find_in_subtree(aid_elems3[0], 'IdValue')
        cid_idval = find_in_subtree(cid_elems2[0], 'IdValue')
        if aid_idval and cid_idval:
            av = get_text(aid_idval[0])
            cv2 = get_text(cid_idval[0])
            if av and cv2 and av != cv2:
                r.error(f"AssignmentId ('{av}') ≠ ContractId ('{cv2}') — doivent être identiques")
            elif av and cv2:
                r.success(f"AssignmentId = ContractId ✓ ('{av}')")

    # ── PositionStatus (ALSTOM) ──
    for ps in find_in_subtree(assignment, 'PositionStatus'):
        code_elems = find_in_subtree(ps, 'Code')
        if code_elems:
            code_val = get_text(code_elems[0])
            if code_val and ' - ' in code_val:
                r.error(f"PositionStatus/Code fusionné : '{code_val}' (Code et Description doivent être séparés)")
            else:
                r.success("PositionStatus/Code correct")

    return r

# ─────────────────────────────────────────────
# EXPORT CSV
# ─────────────────────────────────────────────

def generate_csv(contract_results, syntax_result, filename, file_type):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Rapport validation Pixid XML'])
    writer.writerow(['Fichier', filename, 'Type', file_type, 'Date analyse', datetime.now().strftime('%Y-%m-%d %H:%M')])
    writer.writerow([])
    writer.writerow(['Numéro contrat', 'Statut', 'Score', 'Nb erreurs', 'Nb avertissements', 'Nb OK', 'Niveau', 'Type message', 'Message', 'Détail'])

    for item in syntax_result.errors:
        writer.writerow(['GLOBAL', 'ERREUR', '', '', '', '', 'Syntaxe XML', 'ERR', item['msg'], item.get('detail', '')])
    for item in syntax_result.warnings:
        writer.writerow(['GLOBAL', 'AVERTISSEMENT', '', '', '', '', 'Syntaxe XML', 'WARN', item['msg'], ''])

    for cr in contract_results:
        for item in cr.errors:
            writer.writerow([cr.contract_num, cr.status_label, cr.score, len(cr.errors), len(cr.warnings), len(cr.ok), 'Contrat', 'ERR', item['msg'], item.get('detail', '')])
        for item in cr.warnings:
            writer.writerow([cr.contract_num, cr.status_label, cr.score, len(cr.errors), len(cr.warnings), len(cr.ok), 'Contrat', 'WARN', item['msg'], ''])
        for item in cr.ok:
            writer.writerow([cr.contract_num, cr.status_label, cr.score, len(cr.errors), len(cr.warnings), len(cr.ok), 'Contrat', 'OK', item['msg'], ''])

    return output.getvalue().encode('utf-8-sig')

# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────

st.markdown("""
<div class="validator-header">
    <h1>Pixid XML Validator <span class="version-badge">v7.4.4</span></h1>
    <div class="subtitle">Validation HR-XML SIDES · Contrats · RA · RCV · Factures · Commandes</div>
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("Glissez votre fichier XML Pixid", type=['xml'], label_visibility="collapsed")

if not uploaded:
    st.markdown("""
    <div style="background:var(--surface); border:1px solid var(--border); padding:3rem;
                text-align:center; color:var(--muted); margin-top:1rem;">
        <div style="font-size:2rem; margin-bottom:1rem; opacity:0.3">⬆</div>
        <div style="font-size:0.9rem;">Chargez un fichier XML Pixid pour lancer la validation</div>
        <div style="font-size:0.75rem; margin-top:0.5rem; opacity:0.6;">
            Contrats · Relevés d'activité · RCV · Factures · Commandes
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

content_bytes = uploaded.read()
size_kb = len(content_bytes) / 1024

st.markdown(f"""
<div style="background:var(--surface); border:1px solid var(--border); padding:0.8rem 1.5rem;
            display:flex; align-items:center; gap:2rem; margin-bottom:1.5rem;">
    <div>
        <div style="font-family:JetBrains Mono,monospace; font-size:0.9rem; color:var(--accent);">{uploaded.name}</div>
        <div style="color:var(--muted); font-size:0.72rem;">{size_kb:.1f} Ko</div>
    </div>
</div>
""", unsafe_allow_html=True)

progress_bar = st.progress(0, text="Analyse en cours...")

# Niveau 1 syntaxe
progress_bar.progress(10, text="Vérification syntaxe XML...")
syntax_result, xml_ok = validate_syntax(content_bytes)

if not xml_ok:
    progress_bar.empty()
    for item in syntax_result.errors:
        detail = f"<br><span style='font-size:0.75rem;color:var(--muted);font-family:JetBrains Mono,monospace'>{item['detail']}</span>" if item.get('detail') else ""
        st.markdown(f'<div class="check-item error"><span class="tag tag-error">FATAL</span>{item["msg"]}{detail}</div>', unsafe_allow_html=True)
    st.stop()

# Parse XML
progress_bar.progress(20, text="Parsing XML...")
try:
    root = ET.fromstring(content_bytes.decode('iso-8859-1', errors='replace'))
except:
    try:
        root = ET.fromstring(content_bytes.decode('utf-8', errors='replace'))
    except Exception as e:
        progress_bar.empty()
        st.error(f"Erreur de parsing : {e}")
        st.stop()

file_type = detect_file_type(root)
type_labels = {
    'contrat': '📄 Contrat de mise à disposition',
    'ra_rcv': '⏱ Relevé d\'activité / RCV',
    'facture': '💶 Facture',
    'commande': '📋 Commande',
    'inconnu': '❓ Type non reconnu'
}

# Extraction contrats
progress_bar.progress(30, text="Extraction des contrats...")
assignments = []
for ns_uri in ['http://ns.hr-xml.org/2004-08-02', '']:
    t = f'{{{ns_uri}}}Assignment' if ns_uri else 'Assignment'
    assignments.extend(root.iter(t))
seen_ids = set()
unique_assignments = []
for a in assignments:
    if id(a) not in seen_ids:
        seen_ids.add(id(a))
        unique_assignments.append(a)
assignments = unique_assignments
nb_contrats = len(assignments)

# Validation par contrat
contract_results = []
for i, assignment in enumerate(assignments):
    progress = 30 + int((i / max(nb_contrats, 1)) * 60)
    progress_bar.progress(progress, text=f"Analyse contrat {i+1}/{nb_contrats}...")
    cr = validate_single_contract(assignment, i + 1)
    contract_results.append(cr)

progress_bar.progress(100, text="Analyse terminée ✓")
progress_bar.empty()

# Doublons
num_counts = defaultdict(list)
for cr in contract_results:
    num_counts[cr.contract_num].append(cr.index)
doublons = {num: idxs for num, idxs in num_counts.items() if len(idxs) > 1}

# ─────────────────────────────────────────────
# AFFICHAGE
# ─────────────────────────────────────────────

nb_errors_total = sum(len(cr.errors) for cr in contract_results) + len(syntax_result.errors)
nb_warns_total = sum(len(cr.warnings) for cr in contract_results) + len(syntax_result.warnings)
nb_ok_total = sum(len(cr.ok) for cr in contract_results) + len(syntax_result.ok)
nb_contrats_ok = sum(1 for cr in contract_results if cr.status == 'ok')
nb_contrats_warn = sum(1 for cr in contract_results if cr.status == 'warning')
nb_contrats_err = sum(1 for cr in contract_results if cr.status == 'error')
total_checks = nb_errors_total + nb_warns_total + nb_ok_total
global_score = int(((nb_ok_total + nb_warns_total * 0.5) / max(total_checks, 1)) * 100)
score_color = "var(--ok)" if global_score >= 80 else "var(--warn)" if global_score >= 50 else "var(--accent2)"

# Bandeau info fichier
doublon_html = f'<div style="background:rgba(255,61,113,0.1); border:1px solid rgba(255,61,113,0.3); padding:0.4rem 1rem; color:var(--accent2); font-size:0.85rem; font-weight:600;">⚠ {len(doublons)} numéro(s) en doublon</div>' if doublons else ''
st.markdown(f"""
<div style="display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap;">
    <div style="background:rgba(0,229,255,0.1); border:1px solid rgba(0,229,255,0.3);
                padding:0.4rem 1rem; color:var(--accent); font-size:0.85rem; font-weight:600;">
        {type_labels.get(file_type, file_type)}
    </div>
    <div style="background:var(--surface); border:1px solid var(--border);
                padding:0.4rem 1rem; font-size:0.85rem;">
        <span style="color:var(--muted)">Contrats : </span>
        <span style="font-family:JetBrains Mono,monospace; font-weight:700; color:var(--text)">{nb_contrats}</span>
    </div>
    {doublon_html}
</div>
""", unsafe_allow_html=True)

# Scores
c1, c2, c3, c4, c5 = st.columns(5)
for col, num, label, color in [
    (c1, global_score, "Score global", score_color),
    (c2, nb_contrats_err, "Contrats en erreur", "var(--accent2)"),
    (c3, nb_contrats_warn, "Avec avertissements", "var(--warn)"),
    (c4, nb_contrats_ok, "Contrats conformes", "var(--ok)"),
    (c5, nb_errors_total, "Erreurs totales", "var(--accent2)"),
]:
    with col:
        st.markdown(f"""
        <div class="score-card">
            <div class="score-number" style="color:{color}">{num}</div>
            <div class="score-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Doublons
if doublons:
    st.markdown('<div class="section-title">Numéros de contrats en doublon</div>', unsafe_allow_html=True)
    for num, idxs in doublons.items():
        st.markdown(f"""
        <div class="check-item error">
            <span class="tag tag-error">DOUBLON</span>
            Contrat <span style="font-family:JetBrains Mono,monospace;color:var(--accent)">{num}</span>
            apparaît {len(idxs)} fois dans le fichier
        </div>""", unsafe_allow_html=True)

# Syntaxe globale
with st.expander(f"🔧 Syntaxe XML globale  ·  {len(syntax_result.errors)} erreur(s)  {len(syntax_result.warnings)} avertissement(s)", expanded=len(syntax_result.errors) > 0):
    for item in syntax_result.errors:
        detail = f"<br><span style='color:var(--muted);font-size:0.75rem;font-family:JetBrains Mono,monospace'>{item['detail']}</span>" if item.get('detail') else ""
        st.markdown(f'<div class="check-item error"><span class="tag tag-error">ERR</span>{item["msg"]}{detail}</div>', unsafe_allow_html=True)
    for item in syntax_result.warnings:
        st.markdown(f'<div class="check-item warning"><span class="tag tag-warn">WARN</span>{item["msg"]}</div>', unsafe_allow_html=True)
    for item in syntax_result.ok:
        st.markdown(f'<div class="check-item ok"><span class="tag tag-ok">OK</span>{item["msg"]}</div>', unsafe_allow_html=True)

# Résultats par contrat
st.markdown('<div class="section-title">Résultats par contrat</div>', unsafe_allow_html=True)

col_f1, _ = st.columns([1, 3])
with col_f1:
    filtre = st.selectbox(
        "Filtrer",
        ["Tous les contrats", "❌ Erreurs uniquement", "⚠️ Avertissements uniquement", "✅ Conformes uniquement"],
        label_visibility="collapsed"
    )

filter_map = {
    "Tous les contrats": None,
    "❌ Erreurs uniquement": "error",
    "⚠️ Avertissements uniquement": "warning",
    "✅ Conformes uniquement": "ok"
}
status_filter = filter_map[filtre]
filtered = [cr for cr in contract_results if status_filter is None or cr.status == status_filter]

if filtered:
    # Tableau récapitulatif
    rows_html = ""
    for cr in filtered:
        sc = cr.score
        sc_color = "var(--ok)" if sc >= 80 else "var(--warn)" if sc >= 50 else "var(--accent2)"
        doublon_flag = " 🔁" if cr.contract_num in doublons else ""
        rows_html += f"""
        <tr>
            <td style="color:var(--accent)">{cr.contract_num}{doublon_flag}</td>
            <td class="{'status-error' if cr.status=='error' else 'status-warn' if cr.status=='warning' else 'status-ok'}">{cr.status_label}</td>
            <td style="color:var(--accent2)">{len(cr.errors)}</td>
            <td style="color:var(--warn)">{len(cr.warnings)}</td>
            <td style="color:var(--ok)">{len(cr.ok)}</td>
            <td style="color:{sc_color}">{sc}/100</td>
        </tr>"""

    st.markdown(f"""
    <table class="summary-table">
        <thead><tr>
            <th>Numéro contrat</th><th>Statut</th>
            <th>Erreurs</th><th>Avertissements</th><th>Contrôles OK</th><th>Score</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Détail par contrat</div>', unsafe_allow_html=True)

    for cr in filtered:
        with st.expander(
            f"{cr.status_label}  ·  {cr.contract_num}  ·  {len(cr.errors)} erreur(s)  {len(cr.warnings)} avert.  Score {cr.score}/100",
            expanded=(cr.status == "error")
        ):
            if cr.errors:
                st.markdown('<div class="section-title">Erreurs</div>', unsafe_allow_html=True)
                for item in cr.errors:
                    detail = f"<br><span style='color:var(--muted);font-size:0.75rem;font-family:JetBrains Mono,monospace'>{item['detail']}</span>" if item.get('detail') else ""
                    st.markdown(f'<div class="check-item error"><span class="tag tag-error">ERR</span>{item["msg"]}{detail}</div>', unsafe_allow_html=True)
            if cr.warnings:
                st.markdown('<div class="section-title">Avertissements</div>', unsafe_allow_html=True)
                for item in cr.warnings:
                    st.markdown(f'<div class="check-item warning"><span class="tag tag-warn">WARN</span>{item["msg"]}</div>', unsafe_allow_html=True)
            if cr.ok:
                st.markdown('<div class="section-title">Contrôles passés</div>', unsafe_allow_html=True)
                for item in cr.ok:
                    st.markdown(f'<div class="check-item ok"><span class="tag tag-ok">OK</span>{item["msg"]}</div>', unsafe_allow_html=True)

# Export CSV
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Export du rapport</div>', unsafe_allow_html=True)
csv_data = generate_csv(contract_results, syntax_result, uploaded.name, type_labels.get(file_type, file_type))
st.download_button(
    label="⬇ Télécharger le rapport CSV",
    data=csv_data,
    file_name=f"rapport_{uploaded.name.replace('.xml','')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)

# Verdict final
verdict = "CONFORME" if global_score >= 80 else "ATTENTION" if global_score >= 50 else "NON CONFORME"
st.markdown(f"""
<div class="verdict-box" style="border-left-color:{score_color}">
    <span style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.2em;color:var(--muted)">Verdict final</span>
    <div style="font-size:1.5rem;font-weight:800;color:{score_color};margin-top:0.3rem;">{verdict}</div>
    <div style="color:var(--muted);font-size:0.82rem;margin-top:0.3rem;">
        {nb_contrats} contrat(s) · {nb_contrats_err} en erreur · {nb_contrats_warn} avec avertissements · {nb_contrats_ok} conformes · Score {global_score}/100
    </div>
</div>
""", unsafe_allow_html=True)
