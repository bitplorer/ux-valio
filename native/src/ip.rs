//! String identity for the IP plan variant.
//!
//! The host stores the given ``str``. ``IPv4Address`` / ``IPv6Address`` /
//! ``ip_address`` are the stdlib parsers, not the stored type. This walk
//! matches those parsers for a ``str`` only (no ``int`` / ``bytes``
//! coerce). A slash is rejected. IPv6 scope-id (``%zone``) is accepted
//! the same way ``IPv6Address`` accepts it.

use crate::plan::{FailKind, IpKind};

const HEXTET_COUNT: usize = 8;

/// ``None`` when the string is a valid address for ``kind``.
pub(crate) fn ip_miss(kind: IpKind, text: &str) -> Option<FailKind> {
    let ok = match kind {
        IpKind::V4 => ipv4_ok(text),
        IpKind::V6 => ipv6_ok(text),
        IpKind::Either => ipv4_ok(text) || ipv6_ok(text),
    };
    if ok {
        None
    } else {
        Some(FailKind::NotIp)
    }
}

fn ipv4_ok(text: &str) -> bool {
    if text.is_empty() || text.as_bytes().contains(&b'/') {
        return false;
    }
    let mut count = 0usize;
    for octet in text.split('.') {
        count += 1;
        if count > 4 || !octet_ok(octet) {
            return false;
        }
    }
    count == 4
}

fn octet_ok(octet: &str) -> bool {
    if octet.is_empty() {
        return false;
    }
    if !octet.bytes().all(|byte| byte.is_ascii_digit()) {
        return false;
    }
    if octet.len() > 3 {
        return false;
    }
    if octet != "0" && octet.as_bytes()[0] == b'0' {
        return false;
    }
    match octet.parse::<u16>() {
        Ok(value) => value <= 255,
        Err(_) => false,
    }
}

fn ipv6_ok(text: &str) -> bool {
    if text.is_empty() || text.as_bytes().contains(&b'/') {
        return false;
    }
    let Some(addr) = split_scope(text) else {
        return false;
    };
    ipv6_addr_ok(addr)
}

/// ``None`` when the scope-id is missing or illegal. Otherwise the
/// address half (scope stripped).
fn split_scope(text: &str) -> Option<&str> {
    match text.split_once('%') {
        None => Some(text),
        Some((addr, scope)) => {
            if scope.is_empty() || scope.as_bytes().contains(&b'%') {
                None
            } else {
                Some(addr)
            }
        }
    }
}

fn hextet_ok(part: &str) -> bool {
    if part.is_empty() || part.len() > 4 {
        return false;
    }
    part.bytes()
        .all(|byte| matches!(byte, b'0'..=b'9' | b'a'..=b'f' | b'A'..=b'F'))
}

fn ipv6_addr_ok(ip_str: &str) -> bool {
    if ip_str.is_empty() {
        return false;
    }
    let mut parts: Vec<&str> = ip_str.split(':').collect();
    if parts.len() < 3 {
        return false;
    }
    if parts.last().is_some_and(|part| part.as_bytes().contains(&b'.')) {
        let last = parts.pop().unwrap_or("");
        if !ipv4_ok(last) {
            return false;
        }
        // The dotted suffix becomes two hextets. Validity does not
        // need their numeric value; ``0`` is a legal stand-in.
        parts.push("0");
        parts.push("0");
    }
    if parts.len() > HEXTET_COUNT + 1 {
        return false;
    }
    let mut skip_index: Option<usize> = None;
    let last_middle = parts.len().saturating_sub(1);
    for (index, part) in parts.iter().enumerate().take(last_middle).skip(1) {
        if part.is_empty() {
            if skip_index.is_some() {
                return false;
            }
            skip_index = Some(index);
        }
    }
    let (hi, lo) = if let Some(skip) = skip_index {
        let mut parts_hi = skip;
        let mut parts_lo = parts.len() - skip - 1;
        if parts[0].is_empty() {
            parts_hi -= 1;
            if parts_hi > 0 {
                return false;
            }
        }
        if parts[parts.len() - 1].is_empty() {
            parts_lo -= 1;
            if parts_lo > 0 {
                return false;
            }
        }
        if parts_hi + parts_lo >= HEXTET_COUNT {
            return false;
        }
        (parts_hi, parts_lo)
    } else {
        if parts.len() != HEXTET_COUNT {
            return false;
        }
        if parts[0].is_empty() || parts[parts.len() - 1].is_empty() {
            return false;
        }
        (parts.len(), 0)
    };
    if !parts.iter().take(hi).all(|part| hextet_ok(part)) {
        return false;
    }
    if lo > 0 && !parts[parts.len() - lo..].iter().all(|part| hextet_ok(part)) {
        return false;
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ok(kind: IpKind, text: &str) -> bool {
        ip_miss(kind, text).is_none()
    }

    #[test]
    fn ipv4_matches_dotted_quad_rules() {
        assert!(ok(IpKind::V4, "127.0.0.1"));
        assert!(ok(IpKind::V4, "0.0.0.0"));
        assert!(ok(IpKind::V4, "255.255.255.255"));
        assert!(!ok(IpKind::V4, ""));
        assert!(!ok(IpKind::V4, "127.0.0.01"));
        assert!(!ok(IpKind::V4, "127.0.0.256"));
        assert!(!ok(IpKind::V4, "127.0.0"));
        assert!(!ok(IpKind::V4, "127.0.0.1/32"));
        assert!(!ok(IpKind::V4, "::1"));
        assert!(!ok(IpKind::Either, "127.0.0.01"));
    }

    #[test]
    fn ipv6_matches_compression_scope_and_mapped() {
        assert!(ok(IpKind::V6, "::"));
        assert!(ok(IpKind::V6, "::1"));
        assert!(ok(IpKind::V6, "1::"));
        assert!(ok(IpKind::V6, "fe80::1%eth0"));
        assert!(ok(IpKind::V6, "::ffff:192.0.2.1"));
        assert!(ok(IpKind::V6, "2001:DB8::1"));
        assert!(!ok(IpKind::V6, "fe80::1%"));
        assert!(!ok(IpKind::V6, "fe80::1%a%b"));
        assert!(!ok(IpKind::V6, "127.0.0.1"));
        assert!(!ok(IpKind::V6, "1::2::3"));
        assert!(!ok(IpKind::V6, "::ffff:192.0.2.256"));
        assert!(ok(IpKind::Either, "::1"));
        assert!(ok(IpKind::Either, "127.0.0.1"));
        assert!(!ok(IpKind::Either, "not-an-ip"));
    }
}
