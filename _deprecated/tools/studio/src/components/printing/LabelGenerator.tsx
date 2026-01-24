
import { Document, Page, Text, View, StyleSheet, PDFViewer } from '@react-pdf/renderer';
import { type InventoryItem } from '../../lib/db';

// Styles for standard 1" x 2-5/8" Address Labels (30 per sheet) - Avery 5160
const styles = StyleSheet.create({
    page: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        backgroundColor: '#fff',
        paddingTop: 36, // 0.5 inch
        paddingLeft: 14, // 0.19 inch
    },
    label: {
        width: 189, // 2.625 inch
        height: 72, // 1 inch
        marginRight: 11, // 0.12 inch gap
        marginBottom: 0,
        padding: 5,
        border: '1pt dotted #eee', // Visual Guide
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between'
    },
    qrCode: {
        width: 50,
        height: 50,
        backgroundColor: 'black',
        alignItems: 'center',
        justifyContent: 'center'
    },
    qrText: {
        color: 'white',
        fontSize: 8,
        fontFamily: 'Helvetica-Bold'
    },
    textContainer: {
        flex: 1,
        paddingLeft: 5,
        height: '100%',
        justifyContent: 'center'
    },
    title: {
        fontSize: 10,
        fontFamily: 'Helvetica-Bold',
        marginBottom: 2,
    },
    meta: {
        fontSize: 8,
        color: '#444',
        fontFamily: 'Helvetica',
    },
    id: {
        fontSize: 6,
        color: '#999',
        marginTop: 2,
        fontFamily: 'Courier'
    }
});

export const InventoryLabelDoc = ({ items }: { items: InventoryItem[] }) => (
    <Document>
        <Page size="LETTER" style={styles.page}>
            {items.map((item, i) => (
                <View key={i} style={styles.label}>
                    {/* Placeholder for QR - We'll add real QR later */}
                    <View style={styles.qrCode}>
                        <Text style={styles.qrText}>QR</Text>
                    </View>
                    <View style={styles.textContainer}>
                        <Text style={styles.title}>{item.name.substring(0, 30)}</Text>
                        <Text style={styles.meta}>{item.category}</Text>
                        <Text style={styles.meta}>{item.location ? `@${item.location}` : ''}</Text>
                        <Text style={styles.id}>#{item.id}</Text>
                    </View>
                </View>
            ))}
        </Page>
    </Document>
);

export function LabelGeneratorModal({ items, onClose }: { items: InventoryItem[], onClose: () => void }) {
    return (
        <div className="fixed inset-0 z-50 bg-black/90 flex flex-col">
            <div className="flex justify-between items-center p-4 border-b border-white/10">
                <h2 className="text-xl font-bold text-white">Print Labels ({items.length})</h2>
                <button onClick={onClose} className="text-white hover:text-red-500">Close</button>
            </div>
            <div className="flex-1 bg-gray-800">
                <PDFViewer width="100%" height="100%" className="w-full h-full">
                    <InventoryLabelDoc items={items} />
                </PDFViewer>
            </div>
        </div>
    );
}
