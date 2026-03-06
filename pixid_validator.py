import streamlit as st
import xml.etree.ElementTree as ET
from lxml import etree
import re
from io import BytesIO
from collections import defaultdict

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Pixid XML Validator",
    page_icon="🔍",
    layout="wide"
)

NS = {
    'hr': 'http://ns.hr-xml.org/2004-08-02',
    'oa': 'http://www.openapplications.org/oagis'
}

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

/* Header */
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
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(0,229,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.validator-header h1 {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text);
    margin: 0 0 0.3rem 0;
    letter-spacing: -0.02em;
}
.validator-header .subtitle {
    color: var(--muted);
    font-size: 0.9rem;
    font-weight: 400;
}
.validator-header .version-badge {
    display: inline-block;
    background: rgba(0,229,255,0.1);
    color: var(--accent);
    border: 1px solid rgba(0,229,255,0.3);
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    margin-left: 1rem;
    vertical-align: middle;
}

/* Upload zone */
.stFileUploader > div {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 0 !important;
    transition: border-color 0.2s;
}
.stFileUploader > div:hover {
    border-color: var(--accent) !important;
}

/* Score card */
.score-card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 1.5rem 2rem;
    text-align: center;
    position: relative;
}
.score-number {
    font-size: 3.5rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.score-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--muted);
}

/* Error / warning / ok items */
.check-item {
    background: var(--surface);
    border-left: 3px solid;
    padding: 0.8rem 1.2rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
}
.check-item.error { border-color: var(--accent2); background: rgba(255,61,113,0.05); }
.check-item.warning { border-color: var(--warn); background: rgba(255,170,0,0.05); }
.check-item.ok { border-color: var(--ok); background: rgba(0,224,150,0.05); }
.check-item .tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    padding: 0.1rem 0.4rem;
    margin-right: 0.5rem;
    font-weight: 600;
}
.tag-error { background: var(--accent2); color: #fff; }
.tag-warn { background: var(--warn); color: #000; }
.tag-ok { background: var(--ok); color: #000; }

.section-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--muted);
    margin: 1.5rem 0 0.7rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* Pill counters */
.pill {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
}
.pill-error { background: rgba(255,61,113,0.15); color: var(--accent2); border: 1px solid rgba(255,61,113,0.3); }
.pill-warn { background: rgba(255,170,0,0.15); color: var(--warn); border: 1px solid rgba(255,170,0,0.3); }
.pill-ok { background: rgba(0,224,150,0.15); color: var(--ok); border: 1px solid rgba(0,224,150,0.3); }

/* Hide streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 0 !important;
    font-weight: 700 !important;
    font-family: 'Syne', sans-serif !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    padding: 0.6rem 1.5rem !important;
}
.stButton > button:hover {
    background: #00b8d4 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="validator-header">
    <h1>Pixid XML Validator <span class="version-badge">v7.4.4</span></h1>
    <div class="subtitle">Validation HR-XML SIDES · Contrats · RA · RCV · Factures</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FONCTIONS DE VALIDATION
# ─────────────────────────────────────────────

def fmt(tag):
    return f'<span class="tag tag-error mono">{tag}</span>'

def detect_file_type(root):
    tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
    if 'AssignmentPacket' in ET.tostring(root, encoding='unicode')[:2000]:
        return 'contrat'
    if 'TimeCardPacket' in ET.tostring(root, encoding='unicode')[:2000]:
        txt = ET.tostring(root, encoding='unicode')[:3000]
        if 'Invoice' in txt or 'TotalCharges' in txt:
            return 'facture'
        return 'ra_rcv'
    if 'OrderPacket' in ET.tostring(root, encoding='unicode')[:2000]:
        return 'commande'
    if 'Invoice' in ET.tostring(root, encoding='unicode')[:2000]:
        return 'facture'
    return 'inconnu'

class ValidationResult:
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
    
    @property
    def score(self):
        total = len(self.errors) + len(self.warnings) + len(self.ok)
        if total == 0: return 0
        points = len(self.ok) * 1.0 + len(self.warnings) * 0.5
        return int((points / total) * 100)

def validate_level1_syntax(content_bytes):
    """Niveau 1 : Syntaxe XML pure"""
    r = ValidationResult()
    
    # 1. Encodage déclaré vs réel
    try:
        header = content_bytes[:200].decode('ascii', errors='replace')
        enc_match = re.search(r'encoding=["\']([^"\']+)["\']', header, re.IGNORECASE)
        declared_enc = enc_match.group(1).upper() if enc_match else None
        
        if declared_enc:
            valid_encodings = ['UTF-8', 'ISO-8859-1', 'ISO-8859-15']
            if declared_enc in valid_encodings:
                r.success(f"Encodage déclaré valide : {declared_enc}")
            else:
                r.error(f"Encodage non accepté par Pixid : {declared_enc}", 
                       "Valeurs acceptées : UTF-8, ISO-8859-1, ISO-8859-15")
        else:
            r.warn("Aucun encodage déclaré en entête XML")
        
        # Tester le parsing avec l'encodage déclaré
        try:
            if declared_enc in ['ISO-8859-1', 'ISO-8859-15']:
                content_bytes.decode('iso-8859-1')
                r.success("Contenu décodable en ISO-8859-1")
            else:
                content_bytes.decode('utf-8')
                r.success("Contenu décodable en UTF-8")
        except UnicodeDecodeError as e:
            r.error("Incohérence encodage déclaré vs contenu réel", str(e))
    except Exception as e:
        r.error("Impossible d'analyser l'entête XML", str(e))
    
    # 2. XML bien formé (lxml strict)
    try:
        parser = etree.XMLParser(recover=False)
        etree.fromstring(content_bytes, parser)
        r.success("XML bien formé (balises ouvertes/fermées correctement)")
    except etree.XMLSyntaxError as e:
        msg = str(e)
        line_match = re.search(r'line (\d+)', msg)
        line_info = f" (ligne {line_match.group(1)})" if line_match else ""
        r.error(f"XML mal formé{line_info}", msg)
        return r  # Inutile de continuer si XML invalide
    
    # 3. Caractères interdits
    try:
        text = content_bytes.decode('iso-8859-1', errors='replace')
        # Caractères de contrôle interdits dans XML (sauf tab, LF, CR)
        forbidden = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text)
        if forbidden:
            r.error(f"Caractères de contrôle interdits détectés ({len(forbidden)} occurrence(s))",
                   "Caractères ASCII < 0x20 non autorisés dans XML")
        else:
            r.success("Aucun caractère de contrôle interdit")
        
        # Entités non définies
        bad_entities = re.findall(r'&(?!amp;|lt;|gt;|apos;|quot;|#\d+;|#x[0-9a-fA-F]+;)[a-zA-Z][a-zA-Z0-9]*;', text)
        if bad_entities:
            r.error(f"Entités XML non définies : {set(bad_entities)}")
        else:
            r.success("Aucune entité XML non définie")
            
    except Exception as e:
        r.warn("Impossible de vérifier les caractères", str(e))
    
    # 4. Namespace HR-XML
    try:
        text = content_bytes.decode('iso-8859-1', errors='replace')
        if 'http://ns.hr-xml.org/2004-08-02' in text:
            r.success("Namespace HR-XML SIDES déclaré")
        else:
            r.warn("Namespace HR-XML SIDES absent", "Attendu : http://ns.hr-xml.org/2004-08-02")
    except:
        pass
    
    return r

def validate_level2_structure(root, file_type):
    """Niveau 2 : Structure HR-XML SIDES"""
    r = ValidationResult()
    xml_str = ET.tostring(root, encoding='unicode')
    
    def find_all(tag):
        results = []
        for ns_uri in ['http://ns.hr-xml.org/2004-08-02', '']:
            if ns_uri:
                results.extend(root.iter(f'{{{ns_uri}}}{tag}'))
            else:
                results.extend(root.iter(tag))
        return results
    
    def find_first(tag):
        items = find_all(tag)
        return items[0] if items else None
    
    # PacketInfo
    packets = find_all('PacketInfo')
    if packets:
        r.success(f"PacketInfo présent ({len(packets)} paquet(s))")
        for p in packets:
            pid = find_first_child(p, 'packetId') or find_first_child(p, 'PacketId')
            action = find_first_child(p, 'action') or find_first_child(p, 'Action')
            if pid is None:
                r.error("PacketInfo sans <packetId>")
            if action is None:
                r.error("PacketInfo sans <action>")
    else:
        r.warn("PacketInfo absent")
    
    # Contrôles spécifiques par type
    if file_type == 'contrat':
        validate_contrat_structure(root, r, find_all, find_first)
    elif file_type == 'ra_rcv':
        validate_ra_structure(root, r, find_all, find_first)
    elif file_type == 'facture':
        validate_facture_structure(root, r, find_all, find_first)
    elif file_type == 'commande':
        validate_commande_structure(root, r, find_all, find_first)
    
    return r

def find_first_child(parent, tag):
    if parent is None: return None
    for child in parent:
        local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if local.lower() == tag.lower():
            return child
    return None

def get_text(elem):
    if elem is None: return None
    return (elem.text or '').strip()

def find_in_subtree(root, tag):
    results = []
    for ns_uri in ['http://ns.hr-xml.org/2004-08-02', '']:
        if ns_uri:
            results.extend(root.iter(f'{{{ns_uri}}}{tag}'))
        else:
            results.extend(root.iter(tag))
    return results

def validate_contrat_structure(root, r, find_all, find_first):
    # Assignment
    assignments = find_all('Assignment')
    if not assignments:
        r.error("Balise <Assignment> absente — contrat non reconnu")
        return
    r.success(f"{len(assignments)} contrat(s) <Assignment> trouvé(s)")
    
    for i, assignment in enumerate(assignments):
        prefix = f"Contrat #{i+1}"
        
        # AssignmentId
        aid_elems = find_in_subtree(assignment, 'AssignmentId')
        if not aid_elems:
            r.error(f"{prefix} : <AssignmentId> absent (obligatoire)")
        else:
            aid = aid_elems[0]
            if not aid.get('idOwner'):
                r.error(f"{prefix} : <AssignmentId> sans attribut idOwner")
            else:
                r.success(f"{prefix} : AssignmentId présent avec idOwner")
        
        # ReferenceInformation
        refs = find_in_subtree(assignment, 'ReferenceInformation')
        if not refs:
            r.error(f"{prefix} : <ReferenceInformation> absent (obligatoire)")
        else:
            ref = refs[0]
            r.success(f"{prefix} : ReferenceInformation présent")
            # StaffingCustomerId
            cust_ids = find_in_subtree(ref, 'StaffingCustomerId')
            if not cust_ids:
                r.error(f"{prefix} : <StaffingCustomerId> absent dans ReferenceInformation")
            else:
                if not cust_ids[0].get('idOwner'):
                    r.error(f"{prefix} : StaffingCustomerId sans idOwner")
                else:
                    r.success(f"{prefix} : StaffingCustomerId avec idOwner")
            # StaffingCustomerOrgUnitId
            org_ids = find_in_subtree(ref, 'StaffingCustomerOrgUnitId')
            if not org_ids:
                r.warn(f"{prefix} : <StaffingCustomerOrgUnitId> absent dans ReferenceInformation")
        
        # CustomerReportingRequirements
        crrs = find_in_subtree(assignment, 'CustomerReportingRequirements')
        if not crrs:
            r.error(f"{prefix} : <CustomerReportingRequirements> absent (obligatoire)")
        else:
            crr = crrs[0]
            r.success(f"{prefix} : CustomerReportingRequirements présent")
            # CostCenter cohérence
            cc_code = find_in_subtree(crr, 'CostCenterCode')
            cc_name = find_in_subtree(crr, 'CostCenterName')
            if cc_code and not cc_name:
                r.warn(f"{prefix} : CostCenterCode présent mais CostCenterName absent")
            if cc_name and not cc_code:
                r.warn(f"{prefix} : CostCenterName présent mais CostCenterCode absent")
            if cc_code and cc_name:
                r.success(f"{prefix} : CostCenterCode + CostCenterName présents")
        
        # Rates
        rates = find_in_subtree(assignment, 'Rates')
        if not rates:
            r.error(f"{prefix} : <Rates> absent (obligatoire)")
        else:
            r.success(f"{prefix} : {len(rates)} groupe(s) <Rates>")
            for ri, rate in enumerate(rates):
                rtype = rate.get('rateType', '')
                rstatus = rate.get('rateStatus', '')
                if rtype not in ['bill', 'pay']:
                    r.error(f"{prefix} Rates#{ri+1} : rateType='{rtype}' invalide (bill/pay attendu)")
                if rstatus not in ['proposed', 'agreed']:
                    r.warn(f"{prefix} Rates#{ri+1} : rateStatus='{rstatus}' (proposed/agreed attendu)")
        
        # StaffingShift
        shifts = find_in_subtree(assignment, 'StaffingShift')
        if not shifts:
            r.error(f"{prefix} : <StaffingShift> absent (obligatoire)")
        else:
            weekly_shifts = [s for s in shifts if s.get('shiftPeriod') == 'weekly']
            if len(weekly_shifts) == 0:
                r.error(f"{prefix} : Aucun StaffingShift avec shiftPeriod='weekly'")
            elif len(weekly_shifts) > 1:
                r.error(f"{prefix} : {len(weekly_shifts)} blocs StaffingShift weekly — un seul autorisé")
            else:
                r.success(f"{prefix} : StaffingShift weekly unique et conforme")
            for s in shifts:
                if not s.get('idOwner') and len(find_in_subtree(s, 'Id')) == 0:
                    # Chercher idOwner dans les Id enfants
                    ids = find_in_subtree(s, 'Id')
                    for id_elem in ids:
                        if not id_elem.get('idOwner'):
                            r.warn(f"{prefix} : StaffingShift/Id sans idOwner (EXT0 attendu)")
        
        # AssignmentDateRange
        dates = find_in_subtree(assignment, 'AssignmentDateRange')
        if not dates:
            r.error(f"{prefix} : <AssignmentDateRange> absent (obligatoire)")
        else:
            dr = dates[0]
            start_elems = find_in_subtree(dr, 'StartDate') or find_in_subtree(dr, 'StartDateTime')
            end_elems = find_in_subtree(dr, 'EndDate') or find_in_subtree(dr, 'EndDateTime')
            if not start_elems:
                r.error(f"{prefix} : StartDate absent dans AssignmentDateRange")
            if not end_elems:
                r.warn(f"{prefix} : EndDate absent dans AssignmentDateRange")
            # Format dates
            for date_elem in (start_elems or []) + (end_elems or []):
                val = get_text(date_elem)
                if val and not re.match(r'^\d{4}-\d{2}-\d{2}', val):
                    r.error(f"{prefix} : Format date invalide '{val}' (yyyy-mm-dd attendu)")
                elif val:
                    r.success(f"{prefix} : Format date OK ({val[:10]})")
                    break
        
        # ContractInformation
        ci_elems = find_in_subtree(assignment, 'ContractInformation')
        if not ci_elems:
            r.error(f"{prefix} : <ContractInformation> absent (obligatoire)")
        else:
            ci = ci_elems[0]
            ct = ci.get('contractType', '')
            cs = ci.get('contractStatus', '')
            if ct != 'staffing customer':
                r.error(f"{prefix} : contractType='{ct}' invalide (valeur fixe: 'staffing customer')")
            else:
                r.success(f"{prefix} : contractType='staffing customer' ✓")
            if cs != 'unsigned':
                r.warn(f"{prefix} : contractStatus='{cs}' (attendu: 'unsigned' pour création)")
            else:
                r.success(f"{prefix} : contractStatus='unsigned' ✓")
            
            # ContractId
            cid_elems = find_in_subtree(ci, 'ContractId')
            if not cid_elems:
                r.error(f"{prefix} : <ContractId> absent dans ContractInformation")
            else:
                cid = cid_elems[0]
                if not cid.get('idOwner'):
                    r.error(f"{prefix} : ContractId sans idOwner")
                r.success(f"{prefix} : ContractId présent")
            
            # ContractVersion
            cv_elems = find_in_subtree(ci, 'ContractVersion')
            if cv_elems:
                cv = get_text(cv_elems[0])
                if cv and not re.match(r'^\d{2}$', cv):
                    r.error(f"{prefix} : ContractVersion='{cv}' invalide (2 chiffres attendus: '00', '01'...)")
                else:
                    r.success(f"{prefix} : ContractVersion='{cv}' ✓")
            else:
                r.error(f"{prefix} : <ContractVersion> absent")
            
            # StaffType
            st_elems = find_in_subtree(ci, 'StaffType')
            if st_elems:
                st_val = get_text(st_elems[0])
                if st_val != 'temporary employee':
                    r.error(f"{prefix} : StaffType='{st_val}' invalide (valeur fixe: 'temporary employee')")
                else:
                    r.success(f"{prefix} : StaffType='temporary employee' ✓")
            else:
                r.error(f"{prefix} : <StaffType> absent (obligatoire)")
            
            # LocalContractRequirements → RecourseType
            lcr = find_in_subtree(ci, 'LocalContractRequirements')
            if not lcr:
                r.error(f"{prefix} : <LocalContractRequirements> absent (obligatoire)")
            else:
                r.success(f"{prefix} : LocalContractRequirements présent")
                lct = find_in_subtree(lcr[0], 'LocalContractType')
                if lct:
                    lct_val = get_text(lct[0])
                    if lct_val not in ['DDF', 'DDE', 'DMF', 'DME']:
                        r.error(f"{prefix} : LocalContractType='{lct_val}' invalide (DDF/DDE/DMF/DME)")
                    else:
                        r.success(f"{prefix} : LocalContractType='{lct_val}' ✓")
                recourse = find_in_subtree(lcr[0], 'RecourseType') or find_in_subtree(lcr[0], 'Code')
                if not recourse:
                    r.warn(f"{prefix} : RecourseType/Code absent dans LocalContractRequirements")
        
        # Cohérence AssignmentId == ContractId
        aid_vals = find_in_subtree(assignment, 'AssignmentId')
        cid_vals = find_in_subtree(assignment, 'ContractId')
        if aid_vals and cid_vals:
            aid_idval = find_in_subtree(aid_vals[0], 'IdValue')
            cid_idval = find_in_subtree(cid_vals[0], 'IdValue')
            if aid_idval and cid_idval:
                av = get_text(aid_idval[0])
                cv = get_text(cid_idval[0])
                if av and cv and av != cv:
                    r.error(f"{prefix} : AssignmentId ('{av}') ≠ ContractId ('{cv}') — doivent être identiques")
                elif av and cv:
                    r.success(f"{prefix} : AssignmentId = ContractId ✓ ('{av}')")
        
        # PositionStatus (ALSTOM)
        pos_statuses = find_in_subtree(assignment, 'PositionStatus')
        for ps in pos_statuses:
            code_elems = find_in_subtree(ps, 'Code')
            desc_elems = find_in_subtree(ps, 'Description')
            if code_elems:
                code_val = get_text(code_elems[0])
                if code_val and ' - ' in code_val:
                    r.error(f"{prefix} : PositionStatus/Code contient Code+Description fusionnés : '{code_val}'",
                           "Le code et la description doivent être dans des balises séparées")
                else:
                    r.success(f"{prefix} : PositionStatus/Code correct")
            if not desc_elems or not get_text(desc_elems[0]):
                if code_elems:
                    r.warn(f"{prefix} : PositionStatus/Description vide")

def validate_ra_structure(root, r, find_all, find_first):
    timecards = find_all('TimeCard')
    if not timecards:
        r.error("<TimeCard> absent")
        return
    r.success(f"{len(timecards)} TimeCard(s) trouvé(s)")
    
    for i, tc in enumerate(timecards):
        prefix = f"TimeCard #{i+1}"
        
        # ReportedTime — 1 seule occurrence
        rt_list = find_in_subtree(tc, 'ReportedTime')
        if len(rt_list) == 0:
            r.error(f"{prefix} : <ReportedTime> absent (obligatoire)")
        elif len(rt_list) > 1:
            r.error(f"{prefix} : {len(rt_list)} blocs <ReportedTime> — un seul attendu")
        else:
            r.success(f"{prefix} : ReportedTime unique ✓")
            rt = rt_list[0]
            # TimeInterval
            intervals = find_in_subtree(rt, 'TimeInterval')
            if not intervals:
                r.warn(f"{prefix} : Aucun <TimeInterval> dans ReportedTime")
            else:
                r.success(f"{prefix} : {len(intervals)} TimeInterval(s)")
                for j, ti in enumerate(intervals):
                    ti_prefix = f"{prefix} TI#{j+1}"
                    # Id avec idOwner
                    id_elems = find_in_subtree(ti, 'Id')
                    for id_e in id_elems:
                        if not id_e.get('idOwner'):
                            r.error(f"{ti_prefix} : TimeInterval/Id sans idOwner (EXT0 ou code_EU)")
                    # Duration XOR Quantity
                    dur = find_in_subtree(ti, 'Duration')
                    qty = find_in_subtree(ti, 'Quantity')
                    if dur and qty:
                        r.error(f"{ti_prefix} : Duration ET Quantity présents — exclusifs (un seul)")
                    elif not dur and not qty:
                        r.warn(f"{ti_prefix} : Ni Duration ni Quantity")
                    # RateOrAmount — min 2
                    roa = find_in_subtree(ti, 'RateOrAmount')
                    if len(roa) < 2:
                        r.error(f"{ti_prefix} : {len(roa)} RateOrAmount — minimum 2 requis (rate+amount)")
                    else:
                        types = [e.get('type', '').lower() for e in roa]
                        has_rate = 'rate' in types
                        has_amount = 'amount' in types
                        if not has_rate:
                            r.error(f"{ti_prefix} : Aucun RateOrAmount type='rate'")
                        if not has_amount:
                            r.error(f"{ti_prefix} : Aucun RateOrAmount type='amount'")
                        billed = [e for e in roa if e.get('toBeBilled') == 'true']
                        if not billed:
                            r.warn(f"{ti_prefix} : Aucun RateOrAmount avec toBeBilled='true'")
                        else:
                            r.success(f"{ti_prefix} : RateOrAmount structure OK ({len(roa)} éléments)")
        
        # AdditionalData
        adatas = find_in_subtree(tc, 'AdditionalData')
        if not adatas:
            r.warn(f"{prefix} : <AdditionalData> absent")
        else:
            adata = adatas[0]
            sad = find_in_subtree(adata, 'StaffingAdditionalData')
            if sad:
                crr = find_in_subtree(sad[0], 'CustomerReportingRequirements')
                ref = find_in_subtree(sad[0], 'ReferenceInformation')
                if not crr:
                    r.error(f"{prefix} : CustomerReportingRequirements absent dans AdditionalData")
                else:
                    r.success(f"{prefix} : CustomerReportingRequirements présent dans AdditionalData")
                if not ref:
                    r.warn(f"{prefix} : ReferenceInformation absent dans AdditionalData")

def validate_facture_structure(root, r, find_all, find_first):
    invoices = find_all('Invoice')
    if not invoices:
        r.error("<Invoice> absent")
        return
    r.success(f"{len(invoices)} Invoice(s) trouvée(s)")
    
    for i, inv in enumerate(invoices):
        prefix = f"Facture #{i+1}"
        
        # Header
        headers = find_in_subtree(inv, 'Header')
        if not headers:
            r.error(f"{prefix} : <Header> absent")
        else:
            hdr = headers[0]
            # TotalCharges
            tc_elems = find_in_subtree(hdr, 'TotalCharges')
            if not tc_elems:
                r.warn(f"{prefix} : TotalCharges absent dans Header")
            else:
                r.success(f"{prefix} : TotalCharges présent")
            
            # ReferenceInformation dans Header
            ref = find_in_subtree(hdr, 'ReferenceInformation')
            if not ref:
                r.error(f"{prefix} : ReferenceInformation absent dans Header (obligatoire)")
            else:
                r.success(f"{prefix} : ReferenceInformation présent dans Header")
                ri = ref[0]
                for required in ['StaffingCustomerId', 'StaffingCustomerOrgUnitId', 'StaffingSupplierId']:
                    elems = find_in_subtree(ri, required)
                    if not elems:
                        r.error(f"{prefix} : <{required}> absent dans Header/ReferenceInformation")
                    else:
                        r.success(f"{prefix} : {required} ✓")
        
        # Lines — ReasonCode UL vs CL
        lines = find_all('Line')
        if lines:
            ul_count = 0
            cl_count = 0
            for line in lines:
                rc_elems = find_in_subtree(line, 'ReasonCode')
                for rc in rc_elems:
                    rc_val = get_text(rc)
                    if rc_val == 'UL':
                        ul_count += 1
                    elif rc_val == 'CL':
                        cl_count += 1
            
            if ul_count > 0 and cl_count == 0:
                r.warn(f"{prefix} : Toutes les lignes en ReasonCode='UL' — risque double-comptage si structure imbriquée")
            elif ul_count > 0:
                r.success(f"{prefix} : Mix UL/CL détecté ({ul_count} UL, {cl_count} CL)")
            
            # TimeCard dans facture
            timecards_in_fac = find_all('TimeCard')
            if timecards_in_fac:
                for j, tc in enumerate(timecards_in_fac):
                    reported_times = find_in_subtree(tc, 'ReportedTime')
                    if len(reported_times) > 1:
                        r.error(f"{prefix} TimeCard#{j+1} : {len(reported_times)} ReportedTime — un seul attendu")

def validate_commande_structure(root, r, find_all, find_first):
    orders = find_all('StaffingOrder')
    if not orders:
        r.error("<StaffingOrder> absent")
        return
    r.success(f"{len(orders)} StaffingOrder(s) trouvé(s)")
    
    for i, order in enumerate(orders):
        prefix = f"Commande #{i+1}"
        for req in ['OrderId', 'ReferenceInformation', 'CustomerReportingRequirements', 
                    'OrderClassification', 'StaffingPosition']:
            elems = find_in_subtree(order, req)
            if not elems:
                r.error(f"{prefix} : <{req}> absent (obligatoire)")
            else:
                r.success(f"{prefix} : {req} ✓")

def validate_level3_business(root, file_type):
    """Niveau 3 : Règles métier avancées"""
    r = ValidationResult()
    
    def find_all_in_tree(tag):
        results = []
        for ns_uri in ['http://ns.hr-xml.org/2004-08-02', '']:
            if ns_uri:
                results.extend(root.iter(f'{{{ns_uri}}}{tag}'))
            else:
                results.extend(root.iter(tag))
        return results
    
    # Dates cohérence
    date_pairs = []
    for dr in find_all_in_tree('AssignmentDateRange'):
        starts = find_in_subtree(dr, 'StartDate') + find_in_subtree(dr, 'StartDateTime')
        ends = find_in_subtree(dr, 'EndDate') + find_in_subtree(dr, 'EndDateTime')
        if starts and ends:
            date_pairs.append((get_text(starts[0]), get_text(ends[0])))
    
    for start_str, end_str in date_pairs:
        if start_str and end_str:
            s = start_str[:10]
            e = end_str[:10]
            if re.match(r'\d{4}-\d{2}-\d{2}', s) and re.match(r'\d{4}-\d{2}-\d{2}', e):
                if s > e:
                    r.error(f"Date début ({s}) > Date fin ({e})", "La date de début doit être antérieure à la date de fin")
                else:
                    r.success(f"Cohérence dates : {s} → {e} ✓")
    
    # RatesId = 100010 pour taux de base
    if file_type == 'contrat':
        rates_ids = find_all_in_tree('RatesId')
        has_100010 = any(
            (e.get('idValue') == '100010' or get_text(e) == '100010')
            for e in rates_ids
        )
        id_values_in_rates = find_all_in_tree('IdValue')
        # Chercher dans le contexte Rates
        rates_elems = find_all_in_tree('Rates')
        found_100010 = False
        for rate in rates_elems:
            for child in rate.iter():
                local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if local in ['RatesId', 'IdValue']:
                    if child.get('idValue') == '100010' or get_text(child) == '100010':
                        found_100010 = True
        
        if found_100010:
            r.success("RatesId '100010' trouvé (taux horaire de base)")
        else:
            r.warn("RatesId '100010' non trouvé — vérifier la codification des rubriques")
        
        # BillingMultiplier
        bm_elems = find_all_in_tree('BillingMultiplier')
        if bm_elems:
            for bm in bm_elems:
                if bm.get('percentIndicator') != 'true':
                    r.warn(f"BillingMultiplier sans percentIndicator='true'")
                else:
                    r.success("BillingMultiplier avec percentIndicator='true' ✓")
        else:
            r.warn("Aucun <BillingMultiplier> trouvé dans les Rates")
    
    # StaffingShift — vérification idOwner=EXT0 sur les Id
    for shift in find_all_in_tree('StaffingShift'):
        for id_elem in find_in_subtree(shift, 'Id'):
            owner = id_elem.get('idOwner', '')
            if owner != 'EXT0':
                r.warn(f"StaffingShift/Id avec idOwner='{owner}' (EXT0 attendu)")
            else:
                r.success("StaffingShift/Id idOwner='EXT0' ✓")
            # Vérifier name="MODELE" ou name="CYCLE"
            idvals = find_in_subtree(id_elem, 'IdValue')
            for iv in idvals:
                name_attr = iv.get('name', '')
                if name_attr and name_attr not in ['MODELE', 'CYCLE', '']:
                    r.warn(f"StaffingShift IdValue name='{name_attr}' — valeurs attendues : MODELE, CYCLE")
    
    # Balises vides critiques
    critical_tags = ['AssignmentId', 'ContractId', 'StaffingCustomerId', 'StaffingSupplierId']
    for tag in critical_tags:
        for elem in find_all_in_tree(tag):
            idvals = find_in_subtree(elem, 'IdValue')
            for iv in idvals:
                if not get_text(iv):
                    r.error(f"<{tag}> contient un <IdValue> vide")
                    break
    
    return r

# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="section-title">Charger un fichier XML</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Glissez votre fichier XML Pixid",
        type=['xml'],
        label_visibility="collapsed"
    )

with col2:
    if uploaded:
        st.markdown('<div class="section-title">Fichier chargé</div>', unsafe_allow_html=True)
        content_bytes = uploaded.read()
        size_kb = len(content_bytes) / 1024
        st.markdown(f"""
        <div style="background: var(--surface); border: 1px solid var(--border); padding: 1rem 1.5rem;">
            <div style="font-family: JetBrains Mono, monospace; font-size: 0.85rem; color: var(--accent);">
                {uploaded.name}
            </div>
            <div style="color: var(--muted); font-size: 0.75rem; margin-top: 0.3rem;">
                {size_kb:.1f} Ko · XML
            </div>
        </div>
        """, unsafe_allow_html=True)

if uploaded:
    st.markdown("---")
    
    # Parse XML pour avoir le root
    try:
        root = ET.fromstring(content_bytes.decode('iso-8859-1', errors='replace'))
        parse_ok = True
    except:
        try:
            root = ET.fromstring(content_bytes.decode('utf-8', errors='replace'))
            parse_ok = True
        except Exception as e:
            parse_ok = False
            st.markdown(f"""
            <div class="check-item error">
                <span class="tag tag-error">FATAL</span>
                XML impossible à parser : {str(e)[:200]}
            </div>
            """, unsafe_allow_html=True)
    
    if parse_ok:
        file_type = detect_file_type(root)
        
        type_labels = {
            'contrat': '📄 Contrat de mise à disposition',
            'ra_rcv': '⏱ Relevé d\'activité / RCV',
            'facture': '💶 Facture',
            'commande': '📋 Commande',
            'inconnu': '❓ Type non reconnu'
        }
        
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem;">
            <div style="background:rgba(0,229,255,0.1); border:1px solid rgba(0,229,255,0.3); 
                        padding:0.4rem 1rem; color:var(--accent); font-size:0.85rem; font-weight:600;">
                {type_labels.get(file_type, file_type)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Lancer les 3 niveaux
        r1 = validate_level1_syntax(content_bytes)
        r2 = validate_level2_structure(root, file_type)
        r3 = validate_level3_business(root, file_type)
        
        # Score global
        total_errors = len(r1.errors) + len(r2.errors) + len(r3.errors)
        total_warns = len(r1.warnings) + len(r2.warnings) + len(r3.warnings)
        total_ok = len(r1.ok) + len(r2.ok) + len(r3.ok)
        total = total_errors + total_warns + total_ok
        
        if total > 0:
            score = int(((total_ok + total_warns * 0.5) / total) * 100)
        else:
            score = 100
        
        if score >= 80:
            score_color = "var(--ok)"
            verdict = "CONFORME"
        elif score >= 50:
            score_color = "var(--warn)"
            verdict = "ATTENTION"
        else:
            score_color = "var(--accent2)"
            verdict = "NON CONFORME"
        
        # Affichage scores
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="score-card">
                <div class="score-number" style="color:{score_color}">{score}</div>
                <div class="score-label">Score / 100</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="score-card">
                <div class="score-number" style="color:var(--accent2)">{total_errors}</div>
                <div class="score-label">Erreurs</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="score-card">
                <div class="score-number" style="color:var(--warn)">{total_warns}</div>
                <div class="score-label">Avertissements</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="score-card">
                <div class="score-number" style="color:var(--ok)">{total_ok}</div>
                <div class="score-label">Contrôles OK</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Résultats par niveau
        for level_num, (level_name, result) in enumerate([
            ("Niveau 1 — Syntaxe XML", r1),
            ("Niveau 2 — Structure HR-XML SIDES", r2),
            ("Niveau 3 — Règles métier Pixid", r3)
        ], 1):
            nb_e = len(result.errors)
            nb_w = len(result.warnings)
            nb_ok = len(result.ok)
            
            with st.expander(
                f"{level_name}   •   {nb_e} erreur(s)   {nb_w} avertissement(s)   {nb_ok} OK",
                expanded=(nb_e > 0)
            ):
                if result.errors:
                    st.markdown('<div class="section-title">Erreurs</div>', unsafe_allow_html=True)
                    for item in result.errors:
                        detail = f"<br><span style='color:var(--muted);font-size:0.78rem;font-family:JetBrains Mono,monospace'>{item['detail']}</span>" if item.get('detail') else ""
                        st.markdown(f"""
                        <div class="check-item error">
                            <span class="tag tag-error">ERR</span>
                            {item['msg']}{detail}
                        </div>""", unsafe_allow_html=True)
                
                if result.warnings:
                    st.markdown('<div class="section-title">Avertissements</div>', unsafe_allow_html=True)
                    for item in result.warnings:
                        detail = f"<br><span style='color:var(--muted);font-size:0.78rem;font-family:JetBrains Mono,monospace'>{item['detail']}</span>" if item.get('detail') else ""
                        st.markdown(f"""
                        <div class="check-item warning">
                            <span class="tag tag-warn">WARN</span>
                            {item['msg']}{detail}
                        </div>""", unsafe_allow_html=True)
                
                if result.ok:
                    st.markdown('<div class="section-title">Contrôles passés</div>', unsafe_allow_html=True)
                    for item in result.ok:
                        st.markdown(f"""
                        <div class="check-item ok">
                            <span class="tag tag-ok">OK</span>
                            {item['msg']}
                        </div>""", unsafe_allow_html=True)
        
        # Verdict final
        st.markdown(f"""
        <div style="margin-top:2rem; background:var(--surface2); border:1px solid var(--border);
                    border-left: 4px solid {score_color}; padding:1.5rem 2rem;">
            <span style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.2em;color:var(--muted)">
                Verdict final
            </span>
            <div style="font-size:1.5rem;font-weight:800;color:{score_color};margin-top:0.3rem;">
                {verdict}
            </div>
            <div style="color:var(--muted);font-size:0.82rem;margin-top:0.3rem;">
                {total_errors} erreur(s) bloquante(s) · {total_warns} avertissement(s) · Score {score}/100
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background:var(--surface); border:1px solid var(--border); padding:3rem; 
                text-align:center; color:var(--muted); margin-top:2rem;">
        <div style="font-size:2rem; margin-bottom:1rem; opacity:0.3">⬆</div>
        <div style="font-size:0.9rem;">Chargez un fichier XML Pixid pour lancer la validation</div>
        <div style="font-size:0.75rem; margin-top:0.5rem; opacity:0.6;">
            Contrats · Relevés d'activité · RCV · Factures · Commandes
        </div>
    </div>
    """, unsafe_allow_html=True)
