import streamlit as st
import xml.etree.ElementTree as ET
from lxml import etree
import re
import csv
import io
import copy
import difflib
from datetime import datetime, date

st.set_page_config(page_title="Pixid XML Validator", page_icon="🔍", layout="wide")

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');
:root {
    --bg:#0a0a0f; --surface:#111118; --surface2:#1a1a24; --border:#2a2a3a;
    --accent:#00e5ff; --accent2:#ff3d71; --warn:#ffaa00; --ok:#00e096;
    --text:#e8e8f0; --muted:#6b6b8a;
}
* { font-family:'Syne',sans-serif; }
code,pre,.mono { font-family:'JetBrains Mono',monospace !important; }
.stApp { background:var(--bg); color:var(--text); }
.validator-header {
    background:linear-gradient(135deg,#0a0a0f 0%,#111128 100%);
    border:1px solid var(--border); border-left:4px solid var(--accent);
    padding:2rem 2.5rem; margin-bottom:2rem; position:relative; overflow:hidden;
}
.validator-header h1 { font-size:2rem; font-weight:800; color:var(--text); margin:0 0 0.3rem 0; letter-spacing:-0.02em; }
.validator-header .subtitle { color:var(--muted); font-size:0.9rem; }
.version-badge {
    display:inline-block; background:rgba(0,229,255,0.1); color:var(--accent);
    border:1px solid rgba(0,229,255,0.3); padding:0.2rem 0.7rem;
    font-size:0.75rem; font-family:'JetBrains Mono',monospace;
    margin-left:1rem; vertical-align:middle;
}
.score-card { background:var(--surface); border:1px solid var(--border); padding:1.2rem 1.5rem; text-align:center; }
.score-number { font-size:2.8rem; font-weight:800; font-family:'JetBrains Mono',monospace; line-height:1; margin-bottom:0.3rem; }
.score-label { font-size:0.7rem; text-transform:uppercase; letter-spacing:0.15em; color:var(--muted); }
.check-item { border-left:3px solid; padding:0.6rem 1rem; margin:0.3rem 0; font-size:0.82rem; }
.check-item.error { border-color:var(--accent2); background:rgba(255,61,113,0.05); }
.check-item.warning { border-color:var(--warn); background:rgba(255,170,0,0.05); }
.check-item.ok { border-color:var(--ok); background:rgba(0,224,150,0.05); }
.check-item .tag { font-family:'JetBrains Mono',monospace; font-size:0.72rem; padding:0.1rem 0.4rem; margin-right:0.5rem; font-weight:700; }
.tag-error { background:var(--accent2); color:#fff; }
.tag-warn { background:var(--warn); color:#000; }
.tag-ok { background:var(--ok); color:#000; }
.tag-fix { background:#7c3aed; color:#fff; }
.section-title {
    font-size:0.65rem; text-transform:uppercase; letter-spacing:0.2em;
    color:var(--muted); margin:1.2rem 0 0.6rem 0;
    display:flex; align-items:center; gap:0.5rem;
}
.section-title::after { content:''; flex:1; height:1px; background:var(--border); }
.summary-row {
    display:grid; grid-template-columns:2fr 1.2fr 0.7fr 1.2fr 0.8fr 1fr;
    gap:0.5rem; padding:0.6rem 1rem;
    border-bottom:1px solid var(--border); font-size:0.8rem; align-items:center;
}
.summary-row:hover { background:var(--surface2); }
.summary-header { font-size:0.62rem; text-transform:uppercase; letter-spacing:0.15em; color:var(--muted); background:var(--surface2); border-bottom:2px solid var(--border); }
.status-badge { display:inline-block; padding:0.15rem 0.6rem; font-size:0.7rem; font-family:'JetBrains Mono',monospace; font-weight:700; }
.status-ok { background:rgba(0,224,150,0.15); color:var(--ok); border:1px solid rgba(0,224,150,0.3); }
.status-warn { background:rgba(255,170,0,0.15); color:var(--warn); border:1px solid rgba(255,170,0,0.3); }
.status-error { background:rgba(255,61,113,0.15); color:var(--accent2); border:1px solid rgba(255,61,113,0.3); }
.diff-added { background:rgba(0,224,150,0.1); border-left:3px solid var(--ok); padding:0.3rem 0.8rem; font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:var(--ok); margin:0.1rem 0; white-space:pre-wrap; }
.diff-removed { background:rgba(255,61,113,0.1); border-left:3px solid var(--accent2); padding:0.3rem 0.8rem; font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:var(--accent2); margin:0.1rem 0; white-space:pre-wrap; }
.diff-unchanged { padding:0.1rem 0.8rem; font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:var(--muted); margin:0.1rem 0; white-space:pre-wrap; }
.fix-banner {
    background:rgba(124,58,237,0.1); border:1px solid rgba(124,58,237,0.4);
    border-left:4px solid #7c3aed; padding:1rem 1.5rem; margin:1rem 0;
}
#MainMenu,footer,header { visibility:hidden; }
.stDeployButton { display:none; }
.stButton > button {
    background:var(--accent) !important; color:#000 !important;
    border:none !important; border-radius:0 !important;
    font-weight:700 !important; font-family:'Syne',sans-serif !important;
    letter-spacing:0.05em !important; text-transform:uppercase !important;
    font-size:0.8rem !important; padding:0.6rem 1.5rem !important;
}
.stButton > button:hover { background:#00b8d4 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="validator-header">
    <h1>Pixid XML Validator <span class="version-badge">v7.4.4</span></h1>
    <div class="subtitle">Validation · Correction automatique · HR-XML SIDES · Contrats · RA · RCV · Factures</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# UTILITAIRES XML
# ─────────────────────────────────────────────

def find_in_subtree(parent, tag):
    results = []
    for ns in ['http://ns.hr-xml.org/2004-08-02', '']:
        t = f'{{{ns}}}{tag}' if ns else tag
        results.extend(parent.iter(t))
    seen = set()
    return [e for e in results if id(e) not in seen and not seen.add(id(e))]

def find_all_in_root(root, tag):
    return find_in_subtree(root, tag)

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

def get_local_tag(elem):
    return elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

def get_assignment_id(assignment):
    for aid in find_in_subtree(assignment, 'AssignmentId'):
        for iv in find_in_subtree(aid, 'IdValue'):
            v = get_text(iv)
            if v: return v
    return None

def get_contract_version(assignment):
    for ci in find_in_subtree(assignment, 'ContractInformation'):
        for cv in find_in_subtree(ci, 'ContractVersion'):
            v = get_text(cv)
            if v: return v
    return None

def get_contract_dates(assignment):
    start, end = None, None
    for dr in find_in_subtree(assignment, 'AssignmentDateRange'):
        for tag in ['StartDate', 'StartDateTime']:
            elems = find_in_subtree(dr, tag)
            if elems and get_text(elems[0]):
                start = get_text(elems[0])[:10]; break
        for tag in ['EndDate', 'EndDateTime']:
            elems = find_in_subtree(dr, tag)
            if elems and get_text(elems[0]):
                end = get_text(elems[0])[:10]; break
    return start, end

def get_siret_and_code_client(assignment):
    """Extrait SIRET et code externe client"""
    siret = None
    code_client = None
    # Code externe client dans StaffingCustomerId
    for sc in find_in_subtree(assignment, 'StaffingCustomerId'):
        for iv in find_in_subtree(sc, 'IdValue'):
            v = get_text(iv)
            if v: code_client = v; break
    # SIRET dans StaffingCustomer/LegalId ou StaffingCustomerOrgUnitId
    for org in find_in_subtree(assignment, 'StaffingCustomerOrgUnitId'):
        for iv in find_in_subtree(org, 'IdValue'):
            v = get_text(iv)
            if v: siret = v; break
    return siret, code_client

def detect_file_type(root):
    xml_str = ET.tostring(root, encoding='unicode')[:3000]
    if 'AssignmentPacket' in xml_str: return 'contrat'
    if 'TimeCardPacket' in xml_str:
        return 'facture' if ('Invoice' in xml_str or 'TotalCharges' in xml_str) else 'ra_rcv'
    if 'OrderPacket' in xml_str: return 'commande'
    if 'Invoice' in xml_str: return 'facture'
    return 'inconnu'

def xml_to_str(root, encoding='iso-8859-1'):
    """Sérialise un arbre XML en string avec l'encodage d'origine"""
    try:
        return ET.tostring(root, encoding='unicode', xml_declaration=False)
    except:
        return ''

def pretty_xml(root):
    """Retourne le XML formaté en string"""
    try:
        lxml_tree = etree.fromstring(ET.tostring(root, encoding='unicode').encode('utf-8'))
        etree.indent(lxml_tree, space='  ')
        return etree.tostring(lxml_tree, encoding='unicode', pretty_print=True)
    except:
        return ET.tostring(root, encoding='unicode')

def compute_diff(before_str, after_str):
    """Calcule le diff ligne par ligne entre avant et après"""
    before_lines = before_str.splitlines()
    after_lines = after_str.splitlines()
    diff = list(difflib.unified_diff(before_lines, after_lines, lineterm='', n=2))
    return diff

# ─────────────────────────────────────────────
# CLASSES RÉSULTATS
# ─────────────────────────────────────────────

class ContractResult:
    def __init__(self, contract_id, version, index, start_date=None, end_date=None, siret=None, code_client=None):
        self.contract_id = contract_id or f"Contrat #{index}"
        self.version = version
        self.index = index
        self.start_date = start_date
        self.end_date = end_date
        self.siret = siret
        self.code_client = code_client
        self.errors = []
        self.warnings = []
        self.ok = []
        self.fixes = []  # corrections appliquées

    def error(self, msg, detail="", auto_fixable=False):
        self.errors.append({"msg": msg, "detail": detail, "auto_fixable": auto_fixable})

    def warn(self, msg, detail=""):
        self.warnings.append({"msg": msg, "detail": detail})

    def success(self, msg):
        self.ok.append({"msg": msg})

    def fix(self, msg):
        self.fixes.append({"msg": msg})

    @property
    def status(self):
        if self.errors: return "error"
        if self.warnings: return "warning"
        return "ok"

    @property
    def score(self):
        total = len(self.errors) + len(self.warnings) + len(self.ok)
        if total == 0: return 100
        return int(((len(self.ok) + len(self.warnings) * 0.5) / total) * 100)

    @property
    def label(self):
        v = f" (av.{self.version})" if self.version and self.version != '00' else ""
        return f"{self.contract_id}{v}"

class GlobalResult:
    def __init__(self):
        self.errors = []; self.warnings = []; self.ok = []

    def error(self, msg, detail=""):
        self.errors.append({"msg": msg, "detail": detail})

    def warn(self, msg, detail=""):
        self.warnings.append({"msg": msg, "detail": detail})

    def success(self, msg):
        self.ok.append({"msg": msg})

# ─────────────────────────────────────────────
# CORRECTION AUTOMATIQUE
# ─────────────────────────────────────────────

def auto_fix_xml(content_bytes):
    """
    Applique toutes les corrections automatiques possibles.
    Retourne (fixed_bytes, list_of_fixes)
    """
    fixes = []

    # 1. Réparer XML mal formé avec lxml recover
    try:
        parser = etree.XMLParser(recover=True, encoding='iso-8859-1')
        tree = etree.fromstring(content_bytes, parser)
        # Revérifier si bien formé maintenant
        try:
            etree.XMLParser(recover=False)
            etree.fromstring(content_bytes)
        except:
            fixes.append("XML mal formé réparé (balises non fermées / mal imbriquées)")
    except Exception as e:
        return content_bytes, [f"Impossible de réparer le XML : {e}"]

    # 0. Corriger les balises non fermées AVANT parsing lxml
    # Pattern : <Tag>valeur<Tag> → <Tag>valeur</Tag> (ajout slash uniquement, ligne inchangée)
    import re as _re
    text_raw = content_bytes.decode('iso-8859-1', errors='replace')
    def fix_unclosed_tags(txt):
        fixes_local = []
        # Matche <Tag(attrs)>valeur<Tag> avec > optionnel en fin de ligne
        pattern = _re.compile(r'<([A-Za-z][A-Za-z0-9]*)([^>]*)>([^<]+)<([A-Za-z][A-Za-z0-9]*)>?$', _re.MULTILINE)
        def replacer(m):
            t1, attrs, val, t2 = m.group(1), m.group(2), m.group(3), m.group(4)
            if t1 == t2:
                fixes_local.append(f"Balise non fermee corrigee : <{t1}>{val.strip()}<{t1}> devient <{t1}>{val.strip()}</{t1}>")
                return f'<{t1}{attrs}>{val}</{t1}>'
            return m.group(0)
        result = pattern.sub(replacer, txt)
        return result, fixes_local
    text_raw, unclosed_fixes = fix_unclosed_tags(text_raw)
    if unclosed_fixes:
        fixes.extend(unclosed_fixes)
        content_bytes = text_raw.encode('iso-8859-1', errors='replace')





    # Travailler sur l'arbre lxml
    ns_map = {'hr': 'http://ns.hr-xml.org/2004-08-02'}

    def lxml_find_all(parent, tag):
        results = []
        for ns in ['http://ns.hr-xml.org/2004-08-02', '']:
            t = f'{{{ns}}}{tag}' if ns else tag
            results.extend(parent.iter(t))
        seen = set()
        return [e for e in results if id(e) not in seen and not seen.add(id(e))]

    def lxml_get_text(elem):
        return (elem.text or '').strip() if elem is not None else ''

    # 2. contractType
    for ci in lxml_find_all(tree, 'ContractInformation'):
        if ci.get('contractType', '') != 'staffing customer':
            old = ci.get('contractType', '(absent)')
            ci.set('contractType', 'staffing customer')
            fixes.append(f"contractType corrigé : '{old}' → 'staffing customer'")

    # 3. contractStatus
    for ci in lxml_find_all(tree, 'ContractInformation'):
        if ci.get('contractStatus', '') != 'unsigned':
            old = ci.get('contractStatus', '(absent)')
            ci.set('contractStatus', 'unsigned')
            fixes.append(f"contractStatus corrigé : '{old}' → 'unsigned'")

    # 4. StaffType
    for st_elem in lxml_find_all(tree, 'StaffType'):
        if lxml_get_text(st_elem) != 'temporary employee':
            old = lxml_get_text(st_elem) or '(vide)'
            st_elem.text = 'temporary employee'
            fixes.append(f"StaffType corrigé : '{old}' → 'temporary employee'")

    # 5. ContractVersion — formater sur 2 chiffres
    for cv_elem in lxml_find_all(tree, 'ContractVersion'):
        val = lxml_get_text(cv_elem)
        if val and re.match(r'^\d+$', val) and not re.match(r'^\d{2}$', val):
            old = val
            cv_elem.text = val.zfill(2)
            fixes.append(f"ContractVersion reformaté : '{old}' → '{val.zfill(2)}'")

    # 6. StaffingShift — corriger shiftPeriod si absent ou incorrect
    for shift in lxml_find_all(tree, 'StaffingShift'):
        sp = shift.get('shiftPeriod', '')
        if sp != 'weekly':
            old_val = sp or '(absent)'
            shift.set('shiftPeriod', 'weekly')
            fixes.append(f"shiftPeriod corrige : '{old_val}' -> 'weekly' sur StaffingShift")

    # 7. StaffingShift/Id — corriger idOwner si absent ou different de EXT0
    for shift in lxml_find_all(tree, 'StaffingShift'):
        for id_elem in lxml_find_all(shift, 'Id'):
            owner = id_elem.get('idOwner', '')
            if owner != 'EXT0':
                old_val = owner or '(absent)'
                id_elem.set('idOwner', 'EXT0')
                fixes.append(f"idOwner corrige : '{old_val}' -> 'EXT0' sur StaffingShift/Id")

    # 8. BillingMultiplier — ajouter percentIndicator="true" si absent
    for bm in lxml_find_all(tree, 'BillingMultiplier'):
        if bm.get('percentIndicator') != 'true':
            bm.set('percentIndicator', 'true')
            fixes.append("percentIndicator='true' ajouté sur BillingMultiplier")

    # 9. PositionStatus — séparer Code fusionné avec Description
    for ps in lxml_find_all(tree, 'PositionStatus'):
        for code_elem in lxml_find_all(ps, 'Code'):
            val = lxml_get_text(code_elem)
            if val and ' - ' in val:
                parts = val.split(' - ', 1)
                code_elem.text = parts[0].strip()
                # Chercher ou créer Description
                desc_elems = lxml_find_all(ps, 'Description')
                if desc_elems:
                    if not lxml_get_text(desc_elems[0]):
                        desc_elems[0].text = parts[1].strip()
                else:
                    ns = 'http://ns.hr-xml.org/2004-08-02'
                    desc = etree.SubElement(ps, f'{{{ns}}}Description')
                    desc.text = parts[1].strip()
                fixes.append(f"PositionStatus séparé : Code='{parts[0].strip()}' / Description='{parts[1].strip()}'")

    # 10. CostCenterName absent quand CostCenterCode présent
    for crr in lxml_find_all(tree, 'CustomerReportingRequirements'):
        cc_codes = lxml_find_all(crr, 'CostCenterCode')
        cc_names = lxml_find_all(crr, 'CostCenterName')
        if cc_codes and not cc_names:
            code_val = lxml_get_text(cc_codes[0])
            ns = cc_codes[0].tag.split('}')[0].lstrip('{') if '}' in cc_codes[0].tag else ''
            tag = f'{{{ns}}}CostCenterName' if ns else 'CostCenterName'
            name_elem = etree.SubElement(crr, tag)
            name_elem.text = code_val
            fixes.append(f"CostCenterName ajouté (=CostCenterCode '{code_val}')")

    # 11. Dates — reformater dd/mm/yyyy → yyyy-mm-dd
    for tag in ['StartDate', 'EndDate', 'StartDateTime', 'EndDateTime', 'ContractVersionDate']:
        for elem in lxml_find_all(tree, tag):
            val = lxml_get_text(elem)
            if val and re.match(r'^\d{2}/\d{2}/\d{4}', val):
                parts = val[:10].split('/')
                new_val = f"{parts[2]}-{parts[1]}-{parts[0]}"
                elem.text = new_val + val[10:]
                fixes.append(f"{tag} reformaté : '{val[:10]}' → '{new_val}'")

    # Sérialiser avec l'encodage d'origine
    try:
        header = content_bytes[:200].decode('ascii', errors='replace')
        enc_match = re.search(r'encoding=["\']([^"\']+)["\']', header, re.IGNORECASE)
        declared_enc = enc_match.group(1).lower() if enc_match else 'iso-8859-1'
    except:
        declared_enc = 'iso-8859-1'

    try:
        fixed_bytes = etree.tostring(tree, encoding=declared_enc, xml_declaration=True)
    except:
        fixed_bytes = etree.tostring(tree, encoding='utf-8', xml_declaration=True)

    return fixed_bytes, fixes

# ─────────────────────────────────────────────
# VALIDATION NIVEAU 1
# ─────────────────────────────────────────────

def validate_level1_syntax(content_bytes):
    r = GlobalResult()
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

    try:
        parser = etree.XMLParser(recover=False)
        etree.fromstring(content_bytes, parser)
        r.success("XML bien formé (balises correctement ouvertes/fermées)")
    except etree.XMLSyntaxError as e:
        msg = str(e)
        line_match = re.search(r'line (\d+)', msg)
        line_info = f" (ligne {line_match.group(1)})" if line_match else ""
        r.error(f"XML mal formé{line_info}", msg)
        return r

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
    except Exception as e:
        r.warn("Impossible de vérifier les caractères", str(e))

    try:
        text = content_bytes.decode('iso-8859-1', errors='replace')
        if 'http://ns.hr-xml.org/2004-08-02' in text:
            r.success("Namespace HR-XML SIDES déclaré")
        else:
            r.warn("Namespace HR-XML SIDES absent", "Attendu : http://ns.hr-xml.org/2004-08-02")
    except:
        pass
    return r

# ─────────────────────────────────────────────
# VALIDATION PAR CONTRAT
# ─────────────────────────────────────────────

def validate_single_contract(assignment, index):
    contract_id = get_assignment_id(assignment)
    version = get_contract_version(assignment)
    start_date, end_date = get_contract_dates(assignment)
    siret, code_client = get_siret_and_code_client(assignment)
    r = ContractResult(contract_id, version, index, start_date, end_date, siret, code_client)
    today = date.today().isoformat()

    # AssignmentId
    aids = find_in_subtree(assignment, 'AssignmentId')
    if not aids:
        r.error("<AssignmentId> absent (obligatoire)", auto_fixable=False)
    else:
        if not aids[0].get('idOwner'):
            r.error("<AssignmentId> sans attribut idOwner", auto_fixable=False)
        else:
            r.success(f"AssignmentId · idOwner='{aids[0].get('idOwner')}'")

    # ReferenceInformation
    refs = find_in_subtree(assignment, 'ReferenceInformation')
    if not refs:
        r.error("<ReferenceInformation> absent (obligatoire)")
    else:
        r.success("ReferenceInformation présent")
        cust_ids = find_in_subtree(refs[0], 'StaffingCustomerId')
        if not cust_ids:
            r.error("<StaffingCustomerId> absent dans ReferenceInformation")
        else:
            if not cust_ids[0].get('idOwner'):
                r.error("StaffingCustomerId sans idOwner")
            else:
                r.success(f"StaffingCustomerId · idOwner='{cust_ids[0].get('idOwner')}'")
        if not find_in_subtree(refs[0], 'StaffingCustomerOrgUnitId'):
            r.warn("<StaffingCustomerOrgUnitId> absent dans ReferenceInformation")
        else:
            r.success("StaffingCustomerOrgUnitId présent")

    # CustomerReportingRequirements
    crrs = find_in_subtree(assignment, 'CustomerReportingRequirements')
    if not crrs:
        r.error("<CustomerReportingRequirements> absent (obligatoire)")
    else:
        r.success("CustomerReportingRequirements présent")
        cc_code = find_in_subtree(crrs[0], 'CostCenterCode')
        cc_name = find_in_subtree(crrs[0], 'CostCenterName')
        if cc_code and not cc_name:
            r.warn("CostCenterCode présent mais CostCenterName absent", "Sera corrigé automatiquement")
        elif cc_name and not cc_code:
            r.warn("CostCenterName présent mais CostCenterCode absent")
        elif cc_code and cc_name:
            r.success(f"Centre de coût : '{get_text(cc_code[0])}'")

    # Rates
    rates = find_in_subtree(assignment, 'Rates')
    if not rates:
        r.error("<Rates> absent (obligatoire)")
    else:
        r.success(f"{len(rates)} groupe(s) <Rates>")
        for ri, rate in enumerate(rates):
            rtype = rate.get('rateType', '')
            rstatus = rate.get('rateStatus', '')
            if rtype not in ['bill', 'pay']:
                r.error(f"Rates#{ri+1} : rateType='{rtype}' invalide", "Valeurs : bill / pay")
            if rstatus not in ['proposed', 'agreed']:
                r.warn(f"Rates#{ri+1} : rateStatus='{rstatus}'", "Valeurs : proposed / agreed")
            for amt in find_in_subtree(rate, 'Amount'):
                if get_text(amt) in ['0', '0.0', '0.00', '']:
                    r.warn(f"Rates#{ri+1} : montant à 0 ou vide")
                    break

    # StaffingShift
    shifts = find_in_subtree(assignment, 'StaffingShift')
    if not shifts:
        r.error("<StaffingShift> absent (obligatoire)")
    else:
        weekly = [s for s in shifts if s.get('shiftPeriod') == 'weekly']
        if len(weekly) == 0:
            r.error("Aucun StaffingShift avec shiftPeriod='weekly'", "Sera corrigé automatiquement")
        elif len(weekly) > 1:
            r.error(f"{len(weekly)} blocs StaffingShift weekly — un seul autorisé")
        else:
            r.success("StaffingShift weekly unique ✓")
        for s in shifts:
            for id_e in find_in_subtree(s, 'Id'):
                if id_e.get('idOwner', '') != 'EXT0':
                    r.warn(f"StaffingShift/Id idOwner='{id_e.get('idOwner','')}' (EXT0 attendu)", "Sera corrigé automatiquement")
                for iv in find_in_subtree(id_e, 'IdValue'):
                    na = iv.get('name', '')
                    if na and na not in ['MODELE', 'CYCLE']:
                        r.warn(f"StaffingShift IdValue name='{na}' (MODELE/CYCLE attendu)")

    # AssignmentDateRange
    date_ranges = find_in_subtree(assignment, 'AssignmentDateRange')
    if not date_ranges:
        r.error("<AssignmentDateRange> absent (obligatoire)")
    else:
        dr = date_ranges[0]
        start_elems = find_in_subtree(dr, 'StartDate') + find_in_subtree(dr, 'StartDateTime')
        end_elems = find_in_subtree(dr, 'EndDate') + find_in_subtree(dr, 'EndDateTime')
        if not start_elems:
            r.error("StartDate absent dans AssignmentDateRange")
        else:
            s_val = (get_text(start_elems[0]) or '')[:10]
            if s_val and not re.match(r'^\d{4}-\d{2}-\d{2}', s_val):
                r.error(f"Format StartDate invalide : '{s_val}'", "Format attendu : yyyy-mm-dd — Sera corrigé si dd/mm/yyyy")
            else:
                r.success(f"StartDate : {s_val}")
        if not end_elems:
            r.warn("EndDate absent dans AssignmentDateRange")
        else:
            e_val = (get_text(end_elems[0]) or '')[:10]
            if e_val and not re.match(r'^\d{4}-\d{2}-\d{2}', e_val):
                r.error(f"Format EndDate invalide : '{e_val}'")
            else:
                r.success(f"EndDate : {e_val}")
            if e_val and e_val < today:
                r.warn(f"Contrat expiré — EndDate {e_val} est dans le passé")
        if start_elems and end_elems:
            s = (get_text(start_elems[0]) or '')[:10]
            e = (get_text(end_elems[0]) or '')[:10]
            if s and e and re.match(r'^\d{4}-\d{2}-\d{2}', s) and re.match(r'^\d{4}-\d{2}-\d{2}', e):
                if s > e:
                    r.error(f"Date début ({s}) > Date fin ({e})")
                else:
                    r.success(f"Cohérence dates ✓ ({s} → {e})")

    # ContractInformation
    ci_elems = find_in_subtree(assignment, 'ContractInformation')
    if not ci_elems:
        r.error("<ContractInformation> absent (obligatoire)")
    else:
        ci = ci_elems[0]
        ct = ci.get('contractType', '')
        cs = ci.get('contractStatus', '')
        if ct != 'staffing customer':
            r.error(f"contractType='{ct}' invalide", "Valeur fixe : 'staffing customer' — Sera corrigé automatiquement")
        else:
            r.success("contractType='staffing customer' ✓")
        if cs != 'unsigned':
            r.warn(f"contractStatus='{cs}'", "Attendu : 'unsigned' — Sera corrigé automatiquement")
        else:
            r.success("contractStatus='unsigned' ✓")

        cid_elems = find_in_subtree(ci, 'ContractId')
        if not cid_elems:
            r.error("<ContractId> absent dans ContractInformation")
        else:
            if not cid_elems[0].get('idOwner'):
                r.error("ContractId sans idOwner")
            else:
                r.success(f"ContractId · idOwner='{cid_elems[0].get('idOwner')}'")

        cv_elems = find_in_subtree(ci, 'ContractVersion')
        if cv_elems:
            cv = get_text(cv_elems[0])
            if cv and not re.match(r'^\d{2}$', cv):
                r.error(f"ContractVersion='{cv}' invalide", "2 chiffres — Sera corrigé automatiquement")
            else:
                r.success(f"ContractVersion='{cv}' ✓")
        else:
            r.error("<ContractVersion> absent (obligatoire)")

        st_elems = find_in_subtree(ci, 'StaffType')
        if st_elems:
            sv = get_text(st_elems[0])
            if sv != 'temporary employee':
                r.error(f"StaffType='{sv}' invalide", "Valeur fixe : 'temporary employee' — Sera corrigé automatiquement")
            else:
                r.success("StaffType='temporary employee' ✓")
        else:
            r.error("<StaffType> absent (obligatoire)")

        lcr = find_in_subtree(ci, 'LocalContractRequirements')
        if not lcr:
            r.error("<LocalContractRequirements> absent (obligatoire)")
        else:
            r.success("LocalContractRequirements présent")
            lct_elems = find_in_subtree(lcr[0], 'LocalContractType')
            if lct_elems:
                lct_val = get_text(lct_elems[0])
                if not re.match(r'^(DDF|DDE|DMF|DME)', lct_val or ''):
                    r.error(f"LocalContractType='{lct_val}' invalide",
                            "Préfixe attendu : DDF, DDE, DMF ou DME (variantes -I, -R, -T acceptées)")
                else:
                    r.success(f"LocalContractType='{lct_val}' ✓")
            if not find_in_subtree(lcr[0], 'RecourseType'):
                r.warn("RecourseType absent dans LocalContractRequirements")

    # Cohérence AssignmentId == ContractId
    aid_vals = find_in_subtree(assignment, 'AssignmentId')
    cid_vals = find_in_subtree(assignment, 'ContractId')
    if aid_vals and cid_vals:
        av_list = find_in_subtree(aid_vals[0], 'IdValue')
        cv_list = find_in_subtree(cid_vals[0], 'IdValue')
        if av_list and cv_list:
            av = get_text(av_list[0])
            cv2 = get_text(cv_list[0])
            if av and cv2 and av != cv2:
                r.error(f"AssignmentId ('{av}') ≠ ContractId ('{cv2}')",
                        "Ces deux balises doivent avoir la même valeur")
            elif av and cv2:
                r.success("AssignmentId = ContractId ✓")
        aid_owner = aid_vals[0].get('idOwner', '')
        cid_owner = cid_vals[0].get('idOwner', '') if cid_vals else ''
        if aid_owner and cid_owner and aid_owner != cid_owner:
            r.warn(f"idOwner différent : AssignmentId='{aid_owner}' vs ContractId='{cid_owner}'")

    # PositionStatus
    for ps in find_in_subtree(assignment, 'PositionStatus'):
        for ce in find_in_subtree(ps, 'Code'):
            cv_ps = get_text(ce)
            if cv_ps and ' - ' in cv_ps:
                r.error(f"PositionStatus/Code fusionné : '{cv_ps}'",
                        "Code et Description séparés — Sera corrigé automatiquement")

    # Balises vides critiques
    for tag in ['AssignmentId', 'ContractId', 'StaffingCustomerId', 'StaffingSupplierId']:
        for elem in find_in_subtree(assignment, tag):
            for iv in find_in_subtree(elem, 'IdValue'):
                if not get_text(iv):
                    r.error(f"<{tag}> contient un <IdValue> vide")
                    break

    return r

# ─────────────────────────────────────────────
# VALIDATION GLOBALE
# ─────────────────────────────────────────────

def validate_global(root, file_type, contract_results):
    r = GlobalResult()

    packets = find_all_in_root(root, 'PacketInfo')
    if packets:
        r.success(f"PacketInfo présent ({len(packets)} paquet(s))")
        for p in packets:
            if find_first_child(p, 'packetId') is None:
                r.error("PacketInfo sans <packetId>")
            if find_first_child(p, 'action') is None:
                r.error("PacketInfo sans <action>")
    else:
        r.warn("PacketInfo absent")

    if file_type == 'contrat':
        # Doublons en tenant compte des avenants (AssignmentId + ContractVersion)
        keys_seen = []
        duplicates = []
        for cr in contract_results:
            if cr.contract_id.startswith("Contrat #"):
                continue
            key = f"{cr.contract_id}|{cr.version or '00'}"
            if key in keys_seen:
                duplicates.append(f"{cr.contract_id} (v{cr.version or '00'})")
            keys_seen.append(key)
        if duplicates:
            r.error(f"Doublons exacts (même contrat + même version) : {list(set(duplicates))}")
        else:
            r.success("Aucun doublon contrat+version")

        # RatesId 100010
        found_100010 = any(
            child.get('idValue') == '100010' or get_text(child) == '100010'
            for rate in find_all_in_root(root, 'Rates')
            for child in rate.iter()
            if (child.tag.split('}')[-1] if '}' in child.tag else child.tag) in ['RatesId', 'IdValue']
        )
        if found_100010:
            r.success("RatesId '100010' trouvé (taux horaire de base)")
        else:
            r.warn("RatesId '100010' non trouvé — vérifier la codification des rubriques")

    elif file_type == 'ra_rcv':
        timecards = find_all_in_root(root, 'TimeCard')
        if not timecards:
            r.error("<TimeCard> absent")
        else:
            r.success(f"{len(timecards)} TimeCard(s)")
            for i, tc in enumerate(timecards):
                rt_list = find_in_subtree(tc, 'ReportedTime')
                if len(rt_list) == 0:
                    r.error(f"TimeCard #{i+1} : <ReportedTime> absent")
                elif len(rt_list) > 1:
                    r.error(f"TimeCard #{i+1} : {len(rt_list)} ReportedTime — un seul attendu")
                else:
                    r.success(f"TimeCard #{i+1} : ReportedTime unique ✓")
                    for j, ti in enumerate(find_in_subtree(rt_list[0], 'TimeInterval')):
                        dur = find_in_subtree(ti, 'Duration')
                        qty = find_in_subtree(ti, 'Quantity')
                        if dur and qty:
                            r.error(f"TimeCard #{i+1} TI#{j+1} : Duration ET Quantity — exclusifs")
                        if len(find_in_subtree(ti, 'RateOrAmount')) < 2:
                            r.error(f"TimeCard #{i+1} TI#{j+1} : moins de 2 RateOrAmount")

    elif file_type == 'facture':
        for i, inv in enumerate(find_all_in_root(root, 'Invoice')):
            headers = find_in_subtree(inv, 'Header')
            if not headers:
                r.error(f"Facture #{i+1} : <Header> absent")
            else:
                ref = find_in_subtree(headers[0], 'ReferenceInformation')
                if not ref:
                    r.error(f"Facture #{i+1} : ReferenceInformation absent dans Header")
                else:
                    for req in ['StaffingCustomerId', 'StaffingCustomerOrgUnitId', 'StaffingSupplierId']:
                        if not find_in_subtree(ref[0], req):
                            r.error(f"Facture #{i+1} : <{req}> absent dans Header")
            lines = find_in_subtree(inv, 'Line')
            ul = sum(1 for l in lines for rc in find_in_subtree(l, 'ReasonCode') if get_text(rc) == 'UL')
            cl = sum(1 for l in lines for rc in find_in_subtree(l, 'ReasonCode') if get_text(rc) == 'CL')
            if ul > 0 and cl == 0:
                r.warn(f"Facture #{i+1} : Toutes lignes ReasonCode='UL' — risque double-comptage")

    elif file_type == 'commande':
        for i, order in enumerate(find_all_in_root(root, 'StaffingOrder')):
            for req in ['OrderId', 'ReferenceInformation', 'CustomerReportingRequirements',
                        'OrderClassification', 'StaffingPosition']:
                if not find_in_subtree(order, req):
                    r.error(f"Commande #{i+1} : <{req}> absent (obligatoire)")

    return r

# ─────────────────────────────────────────────
# EXPORT CSV
# ─────────────────────────────────────────────

def generate_csv_report(filename, file_type, r1, r_global, contract_results, fixes_applied):
    output = io.StringIO()
    w = csv.writer(output, delimiter=';')
    w.writerow(['Pixid XML Validator — Rapport'])
    w.writerow(['Fichier', filename])
    w.writerow(['Date', datetime.now().strftime('%d/%m/%Y %H:%M')])
    w.writerow(['Type', file_type])
    w.writerow(['Nb contrats', len(contract_results)])
    w.writerow([])

    if fixes_applied:
        w.writerow(['=== CORRECTIONS APPLIQUÉES ==='])
        for f in fixes_applied:
            w.writerow(['', f])
        w.writerow([])

    w.writerow(['=== RÉSUMÉ GLOBAL ==='])
    w.writerow(['Niveau', 'Type', 'Message', 'Détail'])
    for item in r1.errors:
        w.writerow(['Syntaxe XML', 'ERREUR', item['msg'], item.get('detail', '')])
    for item in r1.warnings:
        w.writerow(['Syntaxe XML', 'AVERTISSEMENT', item['msg'], item.get('detail', '')])
    for item in r_global.errors:
        w.writerow(['Structure globale', 'ERREUR', item['msg'], item.get('detail', '')])
    for item in r_global.warnings:
        w.writerow(['Structure globale', 'AVERTISSEMENT', item['msg'], item.get('detail', '')])
    w.writerow([])

    if contract_results:
        w.writerow(['=== DÉTAIL PAR CONTRAT ==='])
        w.writerow(['N° Contrat', 'Version', 'Code Client', 'Site EU', 'Statut', 'Score',
                    'Date début', 'Date fin', 'Nb Err', 'Nb Avert', 'Type', 'Message', 'Détail'])
        for cr in contract_results:
            sl = {'error': 'NON CONFORME', 'warning': 'ATTENTION', 'ok': 'CONFORME'}[cr.status]
            rows = [(it, 'ERREUR') for it in cr.errors] + [(it, 'AVERTISSEMENT') for it in cr.warnings]
            if not rows:
                w.writerow([cr.contract_id, cr.version or '', cr.code_client or '', cr.siret or '',
                             sl, cr.score, cr.start_date or '', cr.end_date or '', 0, 0, 'OK', 'Conforme', ''])
            else:
                for item, kind in rows:
                    w.writerow([cr.contract_id, cr.version or '', cr.code_client or '', cr.siret or '',
                                 sl, cr.score, cr.start_date or '', cr.end_date or '',
                                 len(cr.errors), len(cr.warnings), kind, item['msg'], item.get('detail', '')])
    return output.getvalue().encode('utf-8-sig')

# ─────────────────────────────────────────────
# RENDU
# ─────────────────────────────────────────────

def render_check_items(items, kind):
    css_map = {'error': ('error', 'tag-error', 'ERR'),
               'warning': ('warning', 'tag-warn', 'WARN'),
               'ok': ('ok', 'tag-ok', 'OK')}
    css, tag_css, tag_label = css_map[kind]
    for item in items:
        detail = f"<br><span style='color:var(--muted);font-size:0.76rem;font-family:JetBrains Mono,monospace'>{item['detail']}</span>" if item.get('detail') else ''
        st.markdown(f"""<div class="check-item {css}">
            <span class="tag {tag_css}">{tag_label}</span>{item['msg']}{detail}</div>""",
                    unsafe_allow_html=True)

def render_result_block(result, show_ok=True):
    if result.errors:
        st.markdown('<div class="section-title">Erreurs</div>', unsafe_allow_html=True)
        render_check_items(result.errors, 'error')
    if result.warnings:
        st.markdown('<div class="section-title">Avertissements</div>', unsafe_allow_html=True)
        render_check_items(result.warnings, 'warning')
    if show_ok and result.ok:
        st.markdown('<div class="section-title">Contrôles passés</div>', unsafe_allow_html=True)
        render_check_items(result.ok, 'ok')

def render_diff(before_str, after_str):
    diff = compute_diff(before_str, after_str)
    if not diff:
        st.info("Aucune différence détectée.")
        return
    html = ""
    for line in diff:
        if line.startswith('+++') or line.startswith('---') or line.startswith('@@'):
            continue
        elif line.startswith('+'):
            html += f'<div class="diff-added">+ {line[1:]}</div>'
        elif line.startswith('-'):
            html += f'<div class="diff-removed">- {line[1:]}</div>'
        else:
            html += f'<div class="diff-unchanged">  {line}</div>'
    st.markdown(html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────

col1, col2 = st.columns([1, 1], gap="large")
with col1:
    st.markdown('<div class="section-title">Charger un fichier XML</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("XML", type=['xml'], label_visibility="collapsed")

with col2:
    if uploaded:
        content_bytes = uploaded.read()
        size_kb = len(content_bytes) / 1024
        st.markdown('<div class="section-title">Fichier chargé</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:var(--surface);border:1px solid var(--border);padding:1rem 1.5rem;">
            <div style="font-family:JetBrains Mono,monospace;font-size:0.85rem;color:var(--accent)">{uploaded.name}</div>
            <div style="color:var(--muted);font-size:0.75rem;margin-top:0.3rem">
                {size_kb:.1f} Ko · XML · {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </div>""", unsafe_allow_html=True)

if uploaded:
    st.markdown("---")

    parse_ok = False
    root = None
    try:
        root = ET.fromstring(content_bytes.decode('iso-8859-1', errors='replace'))
        parse_ok = True
    except:
        try:
            root = ET.fromstring(content_bytes.decode('utf-8', errors='replace'))
            parse_ok = True
        except Exception as e:
            st.markdown(f"""<div class="check-item error">
                <span class="tag tag-error">FATAL</span>XML impossible à parser : {str(e)[:200]}</div>""",
                        unsafe_allow_html=True)
            # Tenter quand même la correction
            st.markdown("""<div class="fix-banner">
                <b style="color:#a78bfa">⚡ Le XML est mal formé.</b>
                La correction automatique peut tenter de le réparer.</div>""", unsafe_allow_html=True)

    # ── CORRECTION AUTOMATIQUE ──
    fixes_applied = []
    fixed_bytes = None
    fixed_root = None

    if st.button("⚡ Corriger automatiquement et télécharger"):
        with st.spinner("Correction en cours..."):
            fixed_bytes, fixes_applied = auto_fix_xml(content_bytes)
            try:
                fixed_root = ET.fromstring(fixed_bytes.decode('iso-8859-1', errors='replace'))
            except:
                try:
                    fixed_root = ET.fromstring(fixed_bytes.decode('utf-8', errors='replace'))
                except:
                    fixed_root = None

        if fixes_applied:
            st.markdown(f"""<div class="fix-banner">
                <b style="color:#a78bfa">⚡ {len(fixes_applied)} correction(s) appliquée(s)</b>
            </div>""", unsafe_allow_html=True)
            for f in fixes_applied:
                st.markdown(f"""<div class="check-item" style="border-color:#7c3aed;background:rgba(124,58,237,0.05)">
                    <span class="tag tag-fix">FIX</span>{f}</div>""", unsafe_allow_html=True)

            # Diff avant / après
            with st.expander("📋 Diff avant / après", expanded=True):
                try:
                    before_str = pretty_xml(root) if root else content_bytes.decode('iso-8859-1', errors='replace')
                    after_str = pretty_xml(fixed_root) if fixed_root else fixed_bytes.decode('iso-8859-1', errors='replace')
                    render_diff(before_str, after_str)
                except Exception as e:
                    st.warning(f"Impossible d'afficher le diff : {e}")

            # Téléchargement XML corrigé
            fname = uploaded.name.replace('.xml', '_corrige.xml')
            st.download_button(
                label="⬇ Télécharger le XML corrigé",
                data=fixed_bytes,
                file_name=fname,
                mime="application/xml"
            )
        else:
            st.success("Aucune correction automatique nécessaire ou applicable.")

    if parse_ok and root is not None:
        file_type = detect_file_type(root)
        type_labels = {
            'contrat': '📄 Contrat de mise à disposition',
            'ra_rcv': '⏱ Relevé d\'activité / RCV',
            'facture': '💶 Facture',
            'commande': '📋 Commande',
            'inconnu': '❓ Type non reconnu'
        }

        assignments = find_all_in_root(root, 'Assignment') if file_type == 'contrat' else []
        nb_contrats = len(assignments)

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;margin:1rem 0;flex-wrap:wrap;">
            <div style="background:rgba(0,229,255,0.1);border:1px solid rgba(0,229,255,0.3);padding:0.4rem 1rem;color:var(--accent);font-size:0.85rem;font-weight:600">
                {type_labels.get(file_type, file_type)}</div>
            {'<div style="background:rgba(0,224,150,0.1);border:1px solid rgba(0,224,150,0.3);padding:0.4rem 1rem;color:var(--ok);font-size:0.85rem;font-weight:600">' + str(nb_contrats) + ' contrat(s)</div>' if nb_contrats > 0 else ''}
        </div>""", unsafe_allow_html=True)

        contract_results = []
        if nb_contrats > 0:
            pb = st.progress(0, text="Analyse en cours...")
            for i, a in enumerate(assignments):
                cr = validate_single_contract(a, i + 1)
                contract_results.append(cr)
                pb.progress((i + 1) / nb_contrats, text=f"Analyse {i+1}/{nb_contrats} — {cr.contract_id}")
            pb.empty()

        r1 = validate_level1_syntax(content_bytes)
        r_global = validate_global(root, file_type, contract_results)

        all_errors = len(r1.errors) + len(r_global.errors) + sum(len(cr.errors) for cr in contract_results)
        all_warns = len(r1.warnings) + len(r_global.warnings) + sum(len(cr.warnings) for cr in contract_results)
        all_ok = len(r1.ok) + len(r_global.ok) + sum(len(cr.ok) for cr in contract_results)
        total = all_errors + all_warns + all_ok
        score = int(((all_ok + all_warns * 0.5) / total) * 100) if total > 0 else 100
        score_color = "var(--ok)" if score >= 80 else "var(--warn)" if score >= 50 else "var(--accent2)"
        verdict = "CONFORME" if score >= 80 else "ATTENTION" if score >= 50 else "NON CONFORME"

        # Scores
        cols = st.columns(5)
        for col, val, label, color in [
            (cols[0], score, "Score / 100", score_color),
            (cols[1], nb_contrats, "Contrats", "var(--accent)"),
            (cols[2], all_errors, "Erreurs", "var(--accent2)"),
            (cols[3], all_warns, "Avertissements", "var(--warn)"),
            (cols[4], all_ok, "Contrôles OK", "var(--ok)"),
        ]:
            with col:
                st.markdown(f"""<div class="score-card">
                    <div class="score-number" style="color:{color}">{val}</div>
                    <div class="score-label">{label}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Export CSV
        csv_data = generate_csv_report(uploaded.name, file_type, r1, r_global, contract_results, fixes_applied)
        st.download_button(
            "⬇ Télécharger le rapport CSV",
            data=csv_data,
            file_name=f"rapport_pixid_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Niveaux globaux
        with st.expander(f"Niveau 1 — Syntaxe XML  •  {len(r1.errors)} erreur(s)  {len(r1.warnings)} avert.",
                         expanded=len(r1.errors) > 0):
            render_result_block(r1)

        with st.expander(f"Niveau 2 — Structure globale  •  {len(r_global.errors)} erreur(s)  {len(r_global.warnings)} avert.",
                         expanded=len(r_global.errors) > 0):
            render_result_block(r_global)

        # Tableau récap contrats
        if contract_results:
            st.markdown('<div class="section-title">Récapitulatif par contrat</div>', unsafe_allow_html=True)

            col_f1, col_f2 = st.columns([1, 1])
            with col_f1:
                filter_status = st.selectbox("Filtrer", ["Tous", "Erreurs uniquement", "Avertissements", "Conformes"],
                                             label_visibility="collapsed")
            with col_f2:
                show_ok_checks = st.selectbox("Détail", ["Erreurs + Avertissements", "Tout afficher"],
                                              label_visibility="collapsed")

            filtered = contract_results
            if filter_status == "Erreurs uniquement":
                filtered = [cr for cr in contract_results if cr.status == 'error']
            elif filter_status == "Avertissements":
                filtered = [cr for cr in contract_results if cr.status == 'warning']
            elif filter_status == "Conformes":
                filtered = [cr for cr in contract_results if cr.status == 'ok']

            st.markdown("""<div class="summary-row summary-header">
                <div>N° Contrat</div><div>Statut</div><div>Score</div>
                <div>Période</div><div>Err/Avert</div><div>Code client / Site</div>
            </div>""", unsafe_allow_html=True)

            for cr in filtered:
                status_css = {'error': 'status-error', 'warning': 'status-warn', 'ok': 'status-ok'}[cr.status]
                status_label = {'error': '❌ NON CONFORME', 'warning': '⚠️ ATTENTION', 'ok': '✅ CONFORME'}[cr.status]
                periode = f"{cr.start_date or '?'} → {cr.end_date or '?'}"
                sc = cr.score
                sc_color = '#ff3d71' if sc < 50 else '#ffaa00' if sc < 80 else '#00e096'
                version_info = f" <span style='color:var(--muted);font-size:0.72rem'>(av.{cr.version})</span>" if cr.version and cr.version != '00' else ""
                client_info = f"{cr.code_client or '—'} / {cr.siret or '—'}"
                st.markdown(f"""<div class="summary-row">
                    <div style="font-family:JetBrains Mono,monospace;font-weight:700;color:var(--accent)">{cr.contract_id}{version_info}</div>
                    <div><span class="status-badge {status_css}">{status_label}</span></div>
                    <div style="font-family:JetBrains Mono,monospace;color:{sc_color};font-weight:700">{sc}/100</div>
                    <div style="color:var(--muted);font-size:0.76rem">{periode}</div>
                    <div style="font-family:JetBrains Mono,monospace">
                        <span style="color:var(--accent2)">{len(cr.errors)}</span>
                        <span style="color:var(--muted)"> / </span>
                        <span style="color:var(--warn)">{len(cr.warnings)}</span>
                    </div>
                    <div style="color:var(--muted);font-size:0.76rem">{client_info}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-title">Détail par contrat</div>', unsafe_allow_html=True)
            show_ok = show_ok_checks == "Tout afficher"

            for cr in filtered:
                bc = '#ff3d71' if cr.status == 'error' else '#ffaa00' if cr.status == 'warning' else '#00e096'
                icon = '❌' if cr.status == 'error' else '⚠️' if cr.status == 'warning' else '✅'
                with st.expander(
                    f"{icon}  {cr.label}  —  {len(cr.errors)} erreur(s)  {len(cr.warnings)} avert.  —  Score {cr.score}/100",
                    expanded=(cr.status == 'error')
                ):
                    periode = f"{cr.start_date or 'N/A'} → {cr.end_date or 'N/A'}"
                    client_str = ""
                    if cr.code_client:
                        client_str += f"<span style='color:var(--muted);font-size:0.76rem;margin-left:1rem'>Code client : {cr.code_client}</span>"
                    if cr.siret:
                        client_str += f"<span style='color:var(--muted);font-size:0.76rem;margin-left:1rem'>Site EU : {cr.siret}</span>"
                    st.markdown(f"""<div style="background:var(--surface2);border-left:4px solid {bc};padding:0.8rem 1.2rem;margin-bottom:1rem">
                        <span style="font-family:JetBrains Mono,monospace;color:var(--accent);font-weight:700;font-size:1rem">{cr.contract_id}</span>
                        <span style="color:var(--muted);font-size:0.76rem;margin-left:1rem">{periode}</span>
                        {client_str}
                    </div>""", unsafe_allow_html=True)
                    render_result_block(cr, show_ok=show_ok)

        # Verdict final
        nb_ok_c = sum(1 for cr in contract_results if cr.status == 'ok')
        nb_w_c = sum(1 for cr in contract_results if cr.status == 'warning')
        nb_e_c = sum(1 for cr in contract_results if cr.status == 'error')
        cs = f"<br>{nb_e_c} contrat(s) non conformes · {nb_w_c} avec avertissements · {nb_ok_c} conformes" if contract_results else ""
        st.markdown(f"""<div style="margin-top:2rem;background:var(--surface2);border:1px solid var(--border);
                    border-left:4px solid {score_color};padding:1.5rem 2rem;">
            <span style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.2em;color:var(--muted)">Verdict final</span>
            <div style="font-size:1.5rem;font-weight:800;color:{score_color};margin-top:0.3rem">{verdict}</div>
            <div style="color:var(--muted);font-size:0.8rem;margin-top:0.4rem">
                {all_errors} erreur(s) · {all_warns} avertissement(s) · Score {score}/100{cs}
            </div>
        </div>""", unsafe_allow_html=True)

else:
    st.markdown("""<div style="background:var(--surface);border:1px solid var(--border);padding:3rem;
                text-align:center;color:var(--muted);margin-top:2rem;">
        <div style="font-size:2rem;margin-bottom:1rem;opacity:0.3">⬆</div>
        <div style="font-size:0.9rem">Chargez un fichier XML Pixid pour lancer la validation</div>
        <div style="font-size:0.75rem;margin-top:0.5rem;opacity:0.6">
            Contrats · Relevés d'activité · RCV · Factures · Commandes
        </div>
    </div>""", unsafe_allow_html=True)
