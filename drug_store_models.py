# -*- coding: utf-8 -*-
from openerp.osv import osv, fields


# ================= NHÀ CUNG CẤP =================
class drug_supplier(osv.osv):
    _name = 'drug.supplier'
    _columns = {
        'code': fields.char(u'Mã NCC', size=20, required=True),
        'name': fields.char(u'Tên nhà cung cấp', size=128, required=True),
        'phone': fields.char(u'Số điện thoại', size=20),
        'address': fields.char(u'Địa chỉ', size=256),
        'email': fields.char(u'Email', size=128),
        'note': fields.text(u'Ghi chú'),
    }



# ================= LOẠI THUỐC =================
class drug_type(osv.osv):
    _name = 'drug.type'
    _columns = {
        'code': fields.char(u'Mã loại', size=10, required=True),
        'name': fields.char(u'Tên loại', size=64, required=True),
        'description': fields.text(u'Ghi chú/Mô tả'),
        'item_ids': fields.one2many('drug.item', 'type_id', u'Danh sách thuốc'),
    }

    def unlink(self, cr, uid, ids, context=None):
        item_obj = self.pool.get('drug.item')
        for cat_id in ids:
            if item_obj.search(cr, uid, [('type_id', '=', cat_id)], count=True) > 0:
                raise osv.except_osv(u'Cảnh báo!', u'Loại thuốc này đang có thuốc, không thể xóa!')
        return super(drug_type, self).unlink(cr, uid, ids, context=context)


# ================= THUỐC =================
class drug_item(osv.osv):
    _name = 'drug.item'
    _columns = {
        'name': fields.char(u'Tên thuốc', size=128, required=True),
        'code': fields.char(u'Mã thuốc', size=32),
        'type_id': fields.many2one('drug.type', u'Loại thuốc', required=True),
        'supplier_id': fields.many2one('drug.supplier', u'Nhà cung cấp'),
        'image': fields.binary(u'Ảnh thuốc'),
        'manufacturer': fields.char(u'Nhà sản xuất', size=64),
        'unit': fields.char(u'Đơn vị tính', size=32),
        'price': fields.float(u'Giá bán'),
        'stock': fields.integer(u'Số lượng tồn'),
        'description': fields.text(u'Mô tả chi tiết'),
    }
    _defaults = {'stock': 0}


# ================= HÓA ĐƠN BÁN THUỐC =================
class drug_receipt(osv.osv):
    _name = 'drug.receipt'
    _columns = {
        'customer_name': fields.char(u'Khách hàng', size=128, required=True),
        'customer_phone': fields.char(u'Số điện thoại', size=20),
        'customer_address': fields.char(u'Địa chỉ', size=256),
        'date': fields.date(u'Ngày bán'),
        'receipt_line_ids': fields.one2many('drug.receipt.line', 'receipt_id', u'Chi tiết hóa đơn'),
        'total_amount': fields.float(u'Tổng tiền', readonly=True),
        'state': fields.selection([
            ('draft', u'Nháp'),
            ('confirmed', u'Đã xác nhận'),
            ('done', u'Hoàn tất'),
        ], u'Trạng thái'),
    }
    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
    }

    def action_confirm(self, cr, uid, ids, context=None):
        for receipt in self.browse(cr, uid, ids, context=context):
            for line in receipt.receipt_line_ids:
                item = line.item_id
                if item and line.quantity:
                    if item.stock < line.quantity:
                        raise osv.except_osv(u'Không đủ số lượng hàng!', u'Thuốc "%s" chỉ còn %d trong kho!' % (item.name, item.stock))
                    self.pool.get('drug.item').write(cr, uid, [item.id], {'stock': item.stock - line.quantity}, context=context)
            total = sum([line.subtotal or 0.0 for line in receipt.receipt_line_ids])
            self.write(cr, uid, [receipt.id], {'state': 'confirmed', 'total_amount': total}, context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)


class drug_receipt_line(osv.osv):
    _name = 'drug.receipt.line'
    _columns = {
        'receipt_id': fields.many2one('drug.receipt', u'Hóa đơn'),
        'item_id': fields.many2one('drug.item', u'Thuốc', required=True),
        'quantity': fields.integer(u'Số lượng', required=True),
        'price_unit': fields.float(u'Đơn giá'),
        'subtotal': fields.float(u'Thành tiền'),
    }
    _defaults = {'quantity': 1}

    def onchange_item_id(self, cr, uid, ids, item_id, context=None):
        if item_id:
            item = self.pool.get('drug.item').browse(cr, uid, item_id, context=context)
            return {'value': {'price_unit': item.price, 'subtotal': item.price * 1}}
        return {'value': {'price_unit': 0.0, 'subtotal': 0.0}}

    def onchange_quantity(self, cr, uid, ids, quantity, price_unit, context=None):
        subtotal = (quantity or 0) * (price_unit or 0)
        return {'value': {'subtotal': subtotal}}


# ================= HÓA ĐƠN NHẬP THUỐC =================
class drug_import_receipt(osv.osv):
    _name = 'drug.import.receipt'
    _columns = {
        'supplier_id': fields.many2one('drug.supplier', u'Nhà cung cấp', required=True),
        'supplier_phone': fields.char(u'SĐT nhà cung cấp', size=20, readonly=True),
        'supplier_address': fields.char(u'Địa chỉ nhà cung cấp', size=256, readonly=True),
        'date': fields.date(u'Ngày nhập'),
        'import_line_ids': fields.one2many('drug.import.receipt.line', 'import_receipt_id', u'Chi tiết nhập'),
        'total_amount': fields.float(u'Tổng tiền', readonly=True),
        'state': fields.selection([
            ('draft', u'Nháp'),
            ('confirmed', u'Đã xác nhận'),
            ('done', u'Hoàn tất'),
        ], u'Trạng thái'),
    }
    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
    }

    def onchange_supplier_id(self, cr, uid, ids, supplier_id, context=None):
        if supplier_id:
            sup = self.pool.get('drug.supplier').browse(cr, uid, supplier_id, context=context)
            return {'value': {'supplier_phone': sup.phone or '', 'supplier_address': sup.address or ''}}
        return {'value': {'supplier_phone': '', 'supplier_address': ''}}

    def action_confirm(self, cr, uid, ids, context=None):
        for receipt in self.browse(cr, uid, ids, context=context):
            for line in receipt.import_line_ids:
                item = line.item_id
                if item and line.quantity:
                    self.pool.get('drug.item').write(cr, uid, [item.id], {'stock': item.stock + line.quantity}, context=context)
            total = sum([line.subtotal or 0.0 for line in receipt.import_line_ids])
            self.write(cr, uid, [receipt.id], {'state': 'confirmed', 'total_amount': total}, context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)


class drug_import_receipt_line(osv.osv):
    _name = 'drug.import.receipt.line'
    _columns = {
        'import_receipt_id': fields.many2one('drug.import.receipt', u'Hóa đơn nhập'),
        'item_id': fields.many2one('drug.item', u'Thuốc', required=True),
        'quantity': fields.integer(u'Số lượng', required=True),
        'price_unit': fields.float(u'Đơn giá'),
        'subtotal': fields.float(u'Thành tiền'),
    }
    _defaults = {'quantity': 1}

    def onchange_item_id(self, cr, uid, ids, item_id, context=None):
        if item_id:
            item = self.pool.get('drug.item').browse(cr, uid, item_id, context=context)
            return {'value': {'price_unit': item.price, 'subtotal': item.price * 1}}
        return {'value': {'price_unit': 0.0, 'subtotal': 0.0}}

    def onchange_quantity(self, cr, uid, ids, quantity, price_unit, context=None):
        subtotal = (quantity or 0) * (price_unit or 0)
        return {'value': {'subtotal': subtotal}}
