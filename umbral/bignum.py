import os
from cryptography.hazmat.backends.openssl import backend


class BigNum(object):
    """
    Represents an OpenSSL BIGNUM except more Pythonic
    """

    def __init__(self, bignum, curve_nid, group, order):
        self.bignum = bignum
        self.curve_nid = curve_nid
        self.group = group
        self.order = order

    @classmethod
    def gen_rand(cls, curve):
        """
        Returns a BigNum object with a cryptographically secure BigNum based
        on the given curve.
        """
        curve_nid = backend._elliptic_curve_to_nid(curve)

        group = backend._lib.EC_GROUP_new_by_curve_name(curve_nid)
        backend.openssl_assert(group != backend._ffi.NULL)

        order = backend._lib.BN_new()
        backend.openssl_assert(order != backend._ffi.NULL)
        order = backend._ffi.gc(order, backend._lib.BN_free)

        with backend._tmp_bn_ctx() as bn_ctx:
            res = backend._lib.EC_GROUP_get_order(group, order, bn_ctx)
            backend.openssl_assert(res == 1)

        order_int = backend._bn_to_int(order)

        # Generate random number on curve
        rand_num = int.from_bytes(os.urandom(curve.key_size // 8), 'big')
        while rand_num >= order_int or rand_num <= 0:
            rand_num = int.from_bytes(os.urandom(curve.key_size // 8), 'big')

        new_rand_bn = backend._int_to_bn(rand_num)
        new_rand_bn = backend._ffi.gc(new_rand_bn, backend._lib.BN_free)

        return BigNum(new_rand_bn, curve_nid, group, order)

    def __int__(self):
        """
        Converts the BigNum to a Python int.
        """
        return backend._bn_to_int(self.bignum)

    def __mul__(self, other):
        """
        Performs a BN_mod_mul between two BIGNUMS.
        """
        product = backend._lib.BN_new()
        backend.openssl_assert(product != backend._ffi.NULL)
        product = backend._ffi.gc(product, backend._lib.BN_free)

        with backend._tmp_bn_ctx() as bn_ctx:
            res = backend._lib.BN_mod_mul(
                product, self.bignum, other.bignum, self.order, bn_ctx
            )
            backend.openssl_assert(res == 1)

        return BigNum(product, self.curve_nid, self.group, self.order)

    def __div__(self, other):
        """
        Performs a BN_div on two BIGNUMs.
        """
        quotient = backend._lib.BN_new()
        backend.openssl_assert(quotient != backend._ffi.NULL)
        quotient = backend._ffi.gc(quotient, backend._lib.BN_free)

        with backend._tmp_bn_ctx() as bn_ctx:
            res = backend._lib.BN_div(
                quotient, backend._ffi.NULL, self.bignum, other.bignum, bn_ctx
            )
            backend.openssl_assert(res == 1)

        return BigNum(quotient, self.curve_nid, self.group, self.order)

    def __inv__(self):
        """
        Performs a BN_mod_inverse.
        """
        with backend._tmp_bn_ctx() as bn_ctx:
            inv = backend._lib.BN_mod_inverse(
                backend._ffi.NULL, self.bignum, self.order, bn_ctx
            )
            backend.openssl_assert(inv != backend._ffi.NULL)
            inv = backend._ffi.gc(inv, backend._lib.BN_free)

        return BigNum(inv, self.curve_nid, self.group, self.order)
